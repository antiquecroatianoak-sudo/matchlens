"""Prospective (truly unseen) test of the locked expanded-v1 configuration.

Workflow, each step append-only:
  snapshot  download the live season files with fetch time and SHA-256
  lock      fit coefficients once on results available before the lock date
  predict   freeze probabilities for upcoming fixtures before kickoff
  score     evaluate frozen predictions once results appear in a later snapshot
Predictions are never rewritten; a fixture already predicted is skipped.
Git commit time is author-controlled; the issue comment carrying the SHA-256 of
the prediction log is the independent timestamp of what was frozen.
"""
import argparse, hashlib, json, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import numpy as np
from analytics.backtest import load_matches, fulltime, LEAGUES, MARKETS
from analytics.expanded_search import features, fit, intensities, probability_array, actual_array, metrics, stripped, FEATURES

ROOT = Path(__file__).resolve().parent.parent
SEASON = '2026-27'
# Leagues whose live season is published as football.json; TR/GR/BE use a TXT
# format not yet parsed and with unresolved sponsor team names.
LIVE = ['en.1', 'it.1', 'es.1', 'de.1', 'fr.1', 'pt.1', 'nl.1']
FRESH_DAYS = 10
MIN_MATCHES = 200
EMBARGO = 2


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def snapshot(out_root):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')
    out = Path(out_root) / stamp
    out.mkdir(parents=True)
    files = []
    for league in LIVE:
        url = f'https://raw.githubusercontent.com/openfootball/football.json/master/{SEASON}/{league}.json'
        data = json.loads(urllib.request.urlopen(url).read())
        path = out / f'{SEASON}-{league}.json'
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        files.append(dict(file=path.name, url=url, sha256=sha(path), fetched_at=now()))
    (out / 'fetch-manifest.json').write_text(json.dumps(dict(source='OpenFootball football.json / CC0', files=files), indent=2) + '\n')
    print(out)
    return out


def fixtures(folder):
    """Listed live-season matches without a result; cancelled/postponed are skipped."""
    out = []
    for path in sorted(Path(folder).glob(f'{SEASON}-*.json')):
        league = path.name[8:-5]
        for item in json.loads(path.read_text())['matches']:
            if fulltime(item) or item.get('status') in ('postponed', 'cancelled', 'abandoned'):
                continue
            key = (league, item['date'], item['team1'], item['team2'])
            out.append(dict(id='|'.join(key), date=item['date'], time=item.get('time'), season=SEASON, league=league,
                            round=item.get('round', ''), home=item['team1'], away=item['team2'], hg=0, ag=0, pending=True))
    return out


def history(snapshot_dir, as_of):
    """Frozen archive plus live results strictly before as_of (results are dated by match day)."""
    rows, _ = load_matches(ROOT / 'data/openfootball')
    live, _ = load_matches(snapshot_dir)
    return [r for r in rows + live if r['date'] < as_of]


def code_hashes():
    return {p: sha(ROOT / p) for p in ('analytics/prospective.py', 'analytics/expanded_search.py', 'analytics/backtest.py')}


def lock(experiment, snapshot_dir, lock_date, source_lock):
    out = Path(experiment)
    if (out / 'prospective-lock.json').exists():
        raise FileExistsError('Lock exists; a new protocol needs a new experiment directory')
    cfg = json.loads(Path(source_lock).read_text())['selected_config']
    rows = history(snapshot_dir, lock_date)
    cutoff = (date.fromisoformat(lock_date) - timedelta(days=EMBARGO)).isoformat()
    records = [r for r in features(rows, cfg['window'], cfg['half_life']) if r['match']['date'] < cutoff]
    model = fit(records, cfg)
    snap = json.loads((Path(snapshot_dir) / 'fetch-manifest.json').read_text())
    doc = dict(
        protocol='prospective-v1', created_at=now(), lock_date=lock_date, source_lock=str(source_lock), config=cfg,
        model=dict(beta=model['beta'].tolist(), center=model['center'].tolist(), scale=model['scale'].tolist(), cols=model['cols'],
                   features=[FEATURES[c] for c in model['cols']], training_matches=len(records),
                   training_last_date=max(r['match']['date'] for r in records)),
        lock_snapshot=dict(dir=str(Path(snapshot_dir).resolve().relative_to(ROOT)), files=snap['files']),
        archive_manifest_sha256=sha(ROOT / 'data/source-manifest.json'), code_sha256=code_hashes(),
        leagues=LIVE, markets=MARKETS, season=SEASON,
        rules=[
            'Only fixtures whose listed date is after the as-of date of the predict run are predicted; each fixture once.',
            'Features use results dated strictly before as_of from the frozen archive and the fetched live snapshot; coefficients never refit.',
            f'Stratum fresh: kickoff minus the older of both teams\' last recorded result <= {FRESH_DAYS} days; otherwise stale. Both strata reported separately and together.',
            'Scoring key is league+season+home+away; a moved fixture is scored only if its actual date is after the prediction as_of.',
            f'No accuracy claim before {MIN_MATCHES} scored matches; even then it is one prospective sample, not proof of profit.',
            'Markets: 1, X, 2, over/under 2.5 regular-time goals only. No odds, ROI or recommendations.',
            'Any change of coefficients, features, grid or rules requires a new experiment directory.'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'prospective-lock.json').write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(training_matches=len(records), training_last_date=doc['model']['training_last_date'], config=cfg)))
    return doc


def load_lock(experiment):
    doc = json.loads((Path(experiment) / 'prospective-lock.json').read_text())
    m = doc['model']
    return doc, dict(beta=np.array(m['beta']), center=np.array(m['center']), scale=np.array(m['scale']), cols=m['cols'])


def predict(experiment, snapshot_dir, as_of, horizon):
    doc, model = load_lock(experiment)
    if as_of < doc['lock_date']:
        raise ValueError('as_of precedes the lock date')
    changed = {p: h for p, h in code_hashes().items() if doc['code_sha256'].get(p) != h}
    if changed:
        raise ValueError('Code changed since lock; create a new experiment before predicting')
    generated_at = now()
    if date.fromisoformat(as_of) != datetime.fromisoformat(generated_at).date():
        raise ValueError('as_of must be the actual UTC generation date; retrospective predictions are not prospective')
    if horizon < 1:
        raise ValueError('horizon must be positive')
    log = Path(experiment) / 'prospective-predictions.jsonl'
    done = {json.loads(line)['key'] for line in log.read_text().splitlines()} if log.exists() else set()
    end = (date.fromisoformat(as_of) + timedelta(days=horizon)).isoformat()
    rows = history(snapshot_dir, as_of)
    upcoming = [f for f in fixtures(snapshot_dir) if as_of < f['date'] <= end]
    cfg = doc['config']
    recs = [r for r in features(rows + upcoming, cfg['window'], cfg['half_life']) if r['match'].get('pending')]
    last = {}
    for r in rows:
        for team in (r['home'], r['away']):
            last[(r['league'], team)] = max(last.get((r['league'], team), ''), r['date'])
    probs = probability_array(intensities(recs, model), cfg['rho'], cfg['temperature']) if recs else []
    made = {r['match']['id'] for r in recs}
    skipped = [dict(id=f['id'], reason='fewer than 5 earlier league results or league history < 100') for f in upcoming if f['id'] not in made]
    snap_sha = sha(Path(snapshot_dir) / 'fetch-manifest.json')
    new = []
    for r, p in zip(recs, probs):
        m = r['match']
        key = '|'.join((m['league'], m['season'], m['home'], m['away']))
        if key in done:
            continue
        older = min(last[(m['league'], m['home'])], last[(m['league'], m['away'])])
        stale = (date.fromisoformat(m['date']) - date.fromisoformat(older)).days
        new.append(dict(key=key, id=m['id'], league=m['league'], season=m['season'], round=m['round'], date=m['date'], time=m['time'],
                        home=m['home'], away=m['away'], as_of=as_of, generated_at=generated_at, history_end=r['history_end'],
                        staleness_days=stale, stratum='fresh' if stale <= FRESH_DAYS else 'stale',
                        prob={k: round(float(v), 6) for k, v in zip(MARKETS, p)}, snapshot_manifest_sha256=snap_sha,
                        protocol=doc['protocol'], status='frozen_before_kickoff'))
    with log.open('a') as f:
        for row in new:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    run = dict(as_of=as_of, horizon_days=horizon, generated_at=now(), snapshot=str(Path(snapshot_dir).resolve().relative_to(ROOT)),
               new_predictions=len(new), already_predicted=len(recs) - len(new), skipped=skipped,
               strata={s: sum(r['stratum'] == s for r in new) for s in ('fresh', 'stale')},
               code_changed_since_lock=changed, log_sha256=sha(log) if log.exists() else None)
    with (Path(experiment) / 'prospective-runs.jsonl').open('a') as f:
        f.write(json.dumps(run, ensure_ascii=False) + '\n')
    print(json.dumps(run, ensure_ascii=False))
    return run


def timing_rejection(prediction, result=None):
    """Date-only sources: require creation before both listed and actual dates.

    A wall-clock time in the source has no verified timezone, so it cannot relax
    the conservative date rule. Invalid legacy records remain in the log.
    """
    try:
        generated = datetime.fromisoformat(prediction['generated_at'].replace('Z', '+00:00'))
        if generated.tzinfo is None or generated.utcoffset() is None:
            return 'generation_timestamp_without_timezone'
        generated_day = generated.astimezone(timezone.utc).date()
        listed_day = date.fromisoformat(prediction['date'])
        as_of = date.fromisoformat(prediction['as_of'])
        if generated_day >= listed_day:
            return 'generated_on_or_after_listed_date'
        if as_of > generated_day or as_of >= listed_day:
            return 'invalid_as_of'
        if result is not None:
            actual_day = date.fromisoformat(result['date'])
            if generated_day >= actual_day or as_of >= actual_day:
                return 'generated_on_or_after_actual_date'
    except (KeyError, TypeError, ValueError, AttributeError):
        return 'invalid_or_missing_timestamp'
    return None


def score(experiment, snapshot_dir):
    log = Path(experiment) / 'prospective-predictions.jsonl'
    preds = [json.loads(line) for line in log.read_text().splitlines()]
    live, _ = load_matches(snapshot_dir)
    results = {'|'.join((r['league'], r['season'], r['home'], r['away'])): r for r in live}
    rejected = []
    eligible = []
    for p in preds:
        reason = timing_rejection(p, results.get(p['key']))
        if reason:
            rejected.append(dict(key=p['key'], reason=reason))
        else:
            eligible.append(p)
    scored = [(p, results[p['key']]) for p in eligible if p['key'] in results]
    def block(pairs):
        if not pairs:
            return None
        pp = np.array([[p['prob'][k] for k in MARKETS] for p, _ in pairs])
        return stripped(metrics(pp, actual_array([dict(match=r) for _, r in pairs])))
    report = dict(generated_at=now(), snapshot=str(Path(snapshot_dir).resolve().relative_to(ROOT)), predictions=len(preds), scored=len(scored),
                  pending=len(eligible) - len(scored), excluded=len(rejected), exclusions=rejected,
                  minimum_for_claims=MIN_MATCHES, enough_for_claims=len(scored) >= MIN_MATCHES,
                  all=block(scored), fresh=block([x for x in scored if x[0]['stratum'] == 'fresh']),
                  stale=block([x for x in scored if x[0]['stratum'] == 'stale']),
                  by_league={code: block([x for x in scored if x[0]['league'] == code]) for code in LIVE},
                  note='Prospective sample; no odds, ROI or recommendations.')
    stamp = Path(snapshot_dir).name
    path = Path(experiment) / f'prospective-score-{stamp}.json'
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('predictions', 'scored', 'pending', 'enough_for_claims')}))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('snapshot'); s.add_argument('--out', default=str(ROOT / 'data/prospective/snapshots'))
    l = sub.add_parser('lock'); l.add_argument('--experiment', required=True); l.add_argument('--snapshot', required=True)
    l.add_argument('--lock-date', required=True); l.add_argument('--source-lock', default=str(ROOT / 'data/experiments/20261028-expanded-v1/expanded-lock.json'))
    q = sub.add_parser('predict'); q.add_argument('--experiment', required=True); q.add_argument('--snapshot', required=True)
    q.add_argument('--as-of', required=True); q.add_argument('--horizon', type=int, default=7)
    c = sub.add_parser('score'); c.add_argument('--experiment', required=True); c.add_argument('--snapshot', required=True)
    a = p.parse_args()
    if a.cmd == 'snapshot':
        snapshot(a.out)
    elif a.cmd == 'lock':
        lock(a.experiment, a.snapshot, a.lock_date, a.source_lock)
    elif a.cmd == 'predict':
        predict(a.experiment, a.snapshot, a.as_of, a.horizon)
    else:
        score(a.experiment, a.snapshot)

