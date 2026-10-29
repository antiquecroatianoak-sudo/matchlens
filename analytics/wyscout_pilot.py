"""Retrospective 2017/18 person-information pilot; NOT an as-published backtest.

Target lineups/coach IDs come from a post-match release. Their historical
publication times are unknown. This intentionally separate ideal-information
experiment cannot certify deployable accuracy or direct player duels.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

FILES = ('England', 'France', 'Germany', 'Italy', 'Spain')
GROUPS = {'baseline': [], 'coach': list(range(15, 23)),
          'players': list(range(23, 29)), 'both': list(range(15, 29))}
BASE = list(range(15))


def normalize(raw_dir):
    """Whitelist input fields: never pass target goals/cards/substitutions as X."""
    rows = []
    seen = set()
    for league in FILES:
        for m in json.loads((Path(raw_dir)/f'matches_{league}.json').read_text()):
            if m['status'] != 'Played' or m['duration'] != 'Regular':
                raise ValueError('Domestic pilot expects completed regular-time fixtures')
            mid = f"wyscout:{m['wyId']}"
            if mid in seen:
                raise ValueError('Duplicate canonical match')
            seen.add(mid)
            sides = {v['side']: v for v in m['teamsData'].values()}
            row = dict(id=mid, league=league, date=m['dateutc'][:10])
            for side in ('home', 'away'):
                t = sides[side]
                lineup = [int(p['playerId']) for p in t['formation']['lineup']]
                if len(lineup) != 11 or len(set(lineup)) != 11:
                    raise ValueError('Invalid starting lineup')
                row[side] = dict(team=int(t['teamId']), coach=int(t['coachId']) or None,
                                 lineup=lineup, score=int(t['score']))
            rows.append(row)
    return sorted(rows, key=lambda r: (r['date'], r['id']))


def points(a, b):
    return 3. if a > b else 1. if a == b else 0.


def build_features(rows):
    """All history excludes the target date and the preceding two days.

    Person residuals use a frozen pre-match Elo expectation of match points.
    Starter residuals are team outcome associations, NOT individual causal
    contributions, shot quality or player-v-player events.
    """
    team_hist = defaultdict(list); coaches = defaultdict(list)
    players = defaultdict(list); elo = defaultdict(lambda: 1500.)
    cursor = 0; records = []
    for target in rows:
        cutoff = (datetime.fromisoformat(target['date'])-timedelta(days=2)).date().isoformat()
        while cursor < len(rows) and rows[cursor]['date'] < cutoff:
            old = rows[cursor]; cursor += 1
            h, a = old['home'], old['away']
            prob = 1/(1+10**(-(elo[h['team']]-elo[a['team']]+65)/400))
            # Fixed draw reference; no target/future estimate of team strength.
            eh = .25+3*.75*prob; ea = .25+3*.75*(1-prob)
            for side, opp, expected in ((h, a, eh), (a, h, ea)):
                entry = dict(date=old['date'], team=side['team'], opponent=opp['team'],
                             coach=side['coach'], lineup=side['lineup'],
                             gf=side['score'], ga=opp['score'],
                             residual=points(side['score'], opp['score'])-expected)
                team_hist[side['team']].append(entry)
                if side['coach']:
                    coaches[side['coach']].append(entry)
                for p in side['lineup']:
                    players[p].append(entry)
            actual = 1. if h['score'] > a['score'] else .5 if h['score'] == a['score'] else 0.
            delta = 20*(actual-prob)
            elo[h['team']] += delta; elo[a['team']] -= delta
        hs, aws = target['home'], target['away']
        if min(len(team_hist[hs['team']]), len(team_hist[aws['team']])) < 5:
            continue
        def shrunk(hist, prior=8):
            weights = [2**(-(datetime.fromisoformat(target['date'])-datetime.fromisoformat(v['date'])).days/120) for v in hist]
            return sum(w*v['residual'] for w,v in zip(weights,hist))/(prior+sum(weights))
        base = []; coach_x = []; player_x = []; supports = []
        for side, opp in ((hs, aws), (aws, hs)):
            hist = team_hist[side['team']]
            for window in (5, 20):
                recent = hist[-window:]
                base += [np.mean([v['gf'] for v in recent]), np.mean([v['ga'] for v in recent])]
            ch = coaches[side['coach']] if side['coach'] else []
            vs = [v for v in ch if v['opponent'] == opp['team']]
            # Require five distinct historical fixtures for opponent effect.
            support = len(vs) >= 5
            supports.append(dict(coach_opponent_matches=len(vs), supported=support,
                                 cross_club_coach=sum(v['team'] != side['team'] for v in ch),
                                 cross_club_player=sum(any(v['team'] != side['team'] for v in players[p]) for p in side['lineup'])))
            coach_x += [shrunk(ch), shrunk(vs) if support else 0.,
                        float(hist[-1]['coach'] != side['coach']), float(side['coach'] is None)]
            ph = [players[p] for p in side['lineup']]
            player_x += [float(np.mean([shrunk(h, 20) for h in ph])),
                         len(set(side['lineup']) & set(hist[-1]['lineup']))/11,
                         sum(not h for h in ph)/11]
        base += [(elo[hs['team']]-elo[aws['team']])/400,
                 min((datetime.fromisoformat(target['date'])-datetime.fromisoformat(team_hist[hs['team']][-1]['date'])).days, 30)/30,
                 min((datetime.fromisoformat(target['date'])-datetime.fromisoformat(team_hist[aws['team']][-1]['date'])).days, 30)/30]
        base += [float(target['league'] == league) for league in FILES[1:]]
        x = base+coach_x+player_x
        assert len(x) == 29
        h, a = hs['score'], aws['score']
        records.append(dict(id=target['id'], date=target['date'], league=target['league'],
                            x=x, y=[0 if h>a else 1 if h==a else 2, int(h+a>2)], support=supports))
    return records


def partition(records):
    return ([r for r in records if r['date'] < '2018-01-01'],
            [r for r in records if '2018-01-01' <= r['date'] < '2018-03-01'],
            [r for r in records if r['date'] >= '2018-03-01'])


def fit_predict(train, targets, group, c, family):
    cols = BASE+GROUPS[group]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000))
    model.fit(np.array([r['x'] for r in train])[:, cols], [r['y'][family] for r in train])
    return model.predict_proba(np.array([r['x'] for r in targets])[:, cols])


def evaluate(p, q, rows):
    y = np.array([r['y'] for r in rows]); offers = np.column_stack([p, 1-q[:, 1], q[:, 1]])
    truth = np.column_stack([y[:, 0] == k for k in range(3)]+[y[:, 1] == 0, y[:, 1] == 1])
    top = offers.argmax(axis=1); hits = int(truth[np.arange(len(rows)), top].sum())
    return dict(matches=len(rows), outcome_accuracy=float(np.mean(p.argmax(axis=1)==y[:, 0])),
                goals_accuracy=float(np.mean(q.argmax(axis=1)==y[:, 1])), top_pick_hits=hits,
                top_pick_misses=len(rows)-hits, top_pick_accuracy=hits/len(rows),
                outcome_log_loss=float(log_loss(y[:, 0], p, labels=[0, 1, 2])),
                goals_log_loss=float(log_loss(y[:, 1], q, labels=[0, 1])),
                brier=float(np.mean((offers-truth)**2)))


def run(raw, output, ui):
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    rows = normalize(raw); records = build_features(rows)
    train, dev, audit = partition(records)
    # No observations near a split boundary enter fitting before two-day embargo.
    train = [r for r in train if r['date'] < '2017-12-30']
    refit = [r for r in records if r['date'] < '2018-02-27']
    trials = []; selected = {}
    for group in GROUPS:
        selected[group] = {}
        for family in range(2):
            candidates = []
            for c in (.01, .1, 1.):
                p = fit_predict(train, dev, group, c, family)
                loss = float(log_loss([r['y'][family] for r in dev], p, labels=list(range(3 if family==0 else 2))))
                trial = dict(group=group, family=family, c=c, development_log_loss=loss)
                candidates.append(trial); trials.append(trial)
            selected[group][str(family)] = min(candidates, key=lambda v:(v['development_log_loss'], v['c']))['c']
    lock = dict(name='wyscout-person-pilot-v1', selected=selected,
                split=dict(train_before='2018-01-01', development_before='2018-03-01', audit_from='2018-03-01'),
                availability='Ideal-information retrospective only; archived pre-match coach/lineup publication unknown.',
                source_sha256=hashlib.sha256((Path(raw)/'matches.zip').read_bytes()).hexdigest(),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    results = {}; predictions = {}
    for group in GROUPS:
        p = fit_predict(refit, audit, group, selected[group]['0'], 0)
        q = fit_predict(refit, audit, group, selected[group]['1'], 1)
        results[group] = evaluate(p, q, audit)
        predictions[group] = dict(outcome=p.tolist(), goals=q.tolist())
    support = [s for r in audit for s in r['support']]
    report = dict(protocol=lock, raw_matches=len(rows), feature_matches=len(records),
                  train_matches=len(train), development_matches=len(dev), audit_matches=len(audit),
                  by_league={league:sum(r['league']==league for r in rows) for league in FILES},
                  trials=trials, results=results, promoted=False,
                  coach_opponent_supported_sides=sum(s['supported'] for s in support),
                  cross_club_coach_sides=sum(s['cross_club_coach']>0 for s in support),
                  cross_club_player_sides=sum(s['cross_club_player']>0 for s in support),
                  direct_player_duel_rows=0,
                  limitations=['Different old cohort: do not compare accuracy to 2024/26 as improvement.',
                               'Coach/lineup publication times unknown; no certified as-of accuracy.',
                               'Player residuals are team outcome associations, not direct duels or causal quality.',
                               'One season gives weak repeated opponent and cross-club history.',
                               'Results are exploratory. No 90% guarantee, exact-score claim, odds or live recommendations.'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'predictions.json').write_text(json.dumps(dict(ids=[r['id'] for r in audit], actual=[r['y'] for r in audit], predictions=predictions))+'\n')
    (out/'normalized.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    if ui:
        Path(ui).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('trials', 'protocol')}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', default='data/wyscout/raw')
    parser.add_argument('--output', required=True)
    parser.add_argument('--ui')
    args = parser.parse_args()
    run(args.raw, args.output, args.ui)
