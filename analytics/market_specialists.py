"""Market-specific learning weights and chronological coefficient refitting.

Uses archived DEVELOPMENT results to seed two configurations, then compares
new training recency/refit rules. Viewed audit seasons are descriptive only.
"""
import argparse
import hashlib
import json
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from analytics.backtest import load_matches, MARKETS, LEAGUES
from analytics.expanded_search import features, arrays, GROUPS, intensities, probability_array, actual_array, metrics, stripped

DEV = ('2022-23', '2023-24')
AUDIT = ('2024-25', '2025-26')
FAMILIES = {'outcome': 'outcome_log_loss', 'goals': 'goals_log_loss'}


def training_rows(records, cutoff):
    """Strict two-day release embargo at every refit, including season edges."""
    last = (date.fromisoformat(cutoff) - timedelta(days=2)).isoformat()
    return [r for r in records if r['match']['date'] < last and not r['match'].get('pending')]


def fit_recency(records, config, cutoff, half_life_days):
    cols = GROUPS[config['group']]
    x, offset, y = arrays(records, cols)
    center = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), 1e-6)
    z = np.column_stack([np.ones(len(x)), (x-center)/scale])
    age = np.array([(date.fromisoformat(cutoff)-date.fromisoformat(r['match']['date'])).days for r in records])
    weight = np.repeat(2.**(-age/half_life_days) if half_life_days else np.ones(len(records)), 2)
    weight /= weight.sum()
    penalty = np.ones(z.shape[1]); penalty[0] = 0
    def objective(beta):
        eta = offset+z@beta
        lam = np.exp(eta)
        return (np.sum(weight*(lam-y*eta))+.5*config['ridge']*np.sum(penalty*beta**2),
                z.T@(weight*(lam-y))+config['ridge']*penalty*beta)
    opt = minimize(objective, np.zeros(z.shape[1]), jac=True, method='L-BFGS-B',
                   bounds=[(-3,3)]*z.shape[1], options={'maxiter':200, 'ftol':1e-10})
    if not opt.success:
        raise RuntimeError(opt.message)
    return dict(beta=opt.x, center=center, scale=scale, cols=cols)


def chronological_predictions(records, season, config, policy):
    targets = [r for r in records if r['match']['season'] == season]
    blocks = {}
    for r in targets:
        # Fit once per season, or again at each calendar quarter's first fixture.
        d = date.fromisoformat(r['match']['date'])
        key = 'season' if policy['refit'] == 'season' else (d.year, (d.month-1)//3)
        blocks.setdefault(key, []).append(r)
    predictions = {}; trace = []
    for block in blocks.values():
        cutoff = min(r['match']['date'] for r in block)
        train = training_rows(records, cutoff)
        model = fit_recency(train, config, cutoff, policy['half_life_days'])
        probs = probability_array(intensities(block, model), config['rho'], config['temperature'])
        predictions.update((r['match']['id'], p) for r,p in zip(block, probs))
        trace.append(dict(cutoff=cutoff, training_matches=len(train), training_last_date=max(r['match']['date'] for r in train), predictions=len(block)))
    return np.array([predictions[r['match']['id']] for r in targets]), targets, trace


def choose(trials, family):
    # No audit fields accepted: deterministic development-only selection.
    field = FAMILIES[family]
    return min(trials, key=lambda t:(np.mean([t['development'][s][field] for s in DEV]), t['id']))


def combine(outcome, goals):
    if len(outcome) != len(goals):
        raise ValueError('Predictions must cover identical fixtures')
    return np.column_stack([outcome[:,:3], goals[:,3:]])


def run(data, archive, output, ui):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    rows, source = load_matches(data)
    archived = [json.loads(line) for line in Path(archive).read_text().splitlines()]
    seeds = {family:min(archived, key=lambda t:np.mean([t['folds'][s][field] for s in DEV]))['config'] for family,field in FAMILIES.items()}
    cache = {}; trials = {}; chosen = {}
    for family, config in seeds.items():
        key = (config['window'], config['half_life'])
        if key not in cache:
            cache[key] = features(rows, *key)
        records = cache[key]
        trials[family] = []
        for recency in (None, 730, 365):
            for refit in ('season', 'quarter'):
                policy = dict(half_life_days=recency, refit=refit)
                trial = dict(id=len(trials[family]), policy=policy, development={}, training_trace={})
                for season in DEV:
                    p, rec, trace = chronological_predictions(records, season, config, policy)
                    trial['development'][season] = stripped(metrics(p, actual_array(rec)))
                    trial['training_trace'][season] = trace
                trials[family].append(trial)
                print(json.dumps(dict(family=family, candidate=trial['id'], policy=policy)), flush=True)
        chosen[family] = choose(trials[family], family)
    protocol = dict(name='market-specialists-v1', created_at=datetime.now(timezone.utc).isoformat(),
                    seed_configs=seeds, chosen=chosen, development_seasons=DEV,
                    archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
                    audit_status='Previously viewed seasons; descriptive only. No independent accuracy claim.',
                    scope='Ten existing leagues, 1X2 and over/under 2.5 only; no external factors added.')
    (out/'specialists-lock.json').write_text(json.dumps(protocol,indent=2)+'\n')
    # Selection is saved before any audit evaluation.
    families = {}; traces = {}; target_ids = None; audit_rec = None
    for family,config in seeds.items():
        parts = []; recs = []; traces[family] = []
        for season in AUDIT:
            p, rec, trace = chronological_predictions(cache[(config['window'],config['half_life'])], season, config, chosen[family]['policy'])
            parts.append(p); recs.extend(rec); traces[family].extend(trace)
        ids = [r['match']['id'] for r in recs]
        if target_ids is not None and ids != target_ids:
            raise ValueError('Market candidates differ in eligible fixtures')
        target_ids = ids; audit_rec = recs; families[family] = np.concatenate(parts)
    combined = combine(families['outcome'], families['goals'])
    truth = actual_array(audit_rec)
    from analytics.expanded_search import fit, records_before
    base_cfg = dict(window=50, half_life=15, ridge=.01, group='snaga', rho=-.1, temperature=1.)
    base_records = cache[(50,15)]
    lookup = {r['match']['id']:r for r in base_records}
    matched = [lookup[i] for i in target_ids]
    base = fit(records_before(base_records, AUDIT[0]), base_cfg)
    reference = probability_array(intensities(matched,base), -.1, 1.)
    report = dict(protocol=protocol, trials=trials, audit=stripped(metrics(combined,truth)),
                  reference=stripped(metrics(reference,truth)), calibration=metrics(combined,truth)['calibration'], audit_training_trace=traces,
                  by_season={}, by_league={}, limitations=[
                      'Seeds and policies selected using viewed development seasons; expanded research, not a fresh final test.',
                      'Audit 2024/25 and 2025/26 already viewed; neither independent proof nor permission for live recommendations.',
                      'Quarterly refits use only results strictly before each cutoff minus two days.',
                      'Weights apply to model training examples, separately from team feature recency.',
                      'No lineups, injuries, tactics, weather, odds or profit test; source coverage remains incomplete.',
                      'Historical source has no first-publication timestamps; two-day availability is a simulation assumption.'])
    for season in AUDIT:
        mask = np.array([r['match']['season']==season for r in audit_rec])
        report['by_season'][season] = dict(candidate=stripped(metrics(combined[mask],truth[mask])), reference=stripped(metrics(reference[mask],truth[mask])))
    for league,name in LEAGUES.items():
        mask = np.array([r['match']['league']==league for r in audit_rec])
        report['by_league'][league] = dict(name=name, candidate=stripped(metrics(combined[mask],truth[mask])), reference=stripped(metrics(reference[mask],truth[mask])))
    (out/'specialists-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if ui:
        Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    with (out/'specialists-predictions.jsonl').open('x') as stream:
        for r,p,y in zip(audit_rec,combined,truth):
            stream.write(json.dumps(dict(id=r['match']['id'], date=r['match']['date'],prob=dict(zip(MARKETS,p.tolist())), actual=dict(zip(MARKETS,y.tolist()))))+'\n')
    print(json.dumps(dict(audit=report['audit'],reference=report['reference'])),flush=True)
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',default='data/openfootball')
    parser.add_argument('--archive',default='data/experiments/20261028-expanded-v1/expanded-trials.jsonl')
    parser.add_argument('--output',required=True)
    parser.add_argument('--ui')
    args=parser.parse_args()
    run(args.data,args.archive,args.output,args.ui)
