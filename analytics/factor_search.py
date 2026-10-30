"""New historical-factor ablations and nonlinear learners; no live predictions.

Tune on 2022/23, calibrate 2023/24; viewed 2024/25-2025/26 are descriptive.
All feature histories have a strict two-day embargo, no random time splits.
"""
import argparse
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from scipy.special import softmax, expit
from analytics.backtest import load_matches, MARKETS, LEAGUES
from analytics.direct_model import history_extras, design
from analytics.expanded_search import features, actual_array, metrics, stripped, records_before, fit, intensities, probability_array

GROUPS = {
    'strength': list(range(6)), 'existing_history': list(range(38)), 'all': list(range(84)),
    'without_league': [i for i in range(84) if not 38 <= i < 48],
    'without_multiscale': [i for i in range(84) if not 48 <= i < 78],
    'without_league_trend': [i for i in range(84) if not 78 <= i < 82],
    'without_calendar': list(range(82)),
}


def extra_factors(rows, records):
    """46 new values: league identity, team horizons, league trend, season phase."""
    by_league=defaultdict(list); targets=defaultdict(list); output={}
    for row in rows: by_league[row['league']].append(row)
    for record in records: targets[record['match']['league']].append(record)
    league_ids=sorted(LEAGUES)
    for league, matches in by_league.items():
        ordered=sorted(matches,key=lambda r:(r['date'],r['id']))
        teams=defaultdict(list); past=[]; cursor=0
        for record in sorted(targets[league],key=lambda r:(r['match']['date'],r['match']['id'])):
            match=record['match']; day=date.fromisoformat(match['date'])
            cutoff=(day-timedelta(days=2)).isoformat()
            while cursor<len(ordered) and ordered[cursor]['date']<cutoff:
                row=ordered[cursor];cursor+=1
                if row.get('pending'): continue
                teams[row['home']].append((row['hg'],row['ag']))
                teams[row['away']].append((row['ag'],row['hg']))
                past.append(row)
            mean=np.mean([r['hg']+r['ag'] for r in past[-40:]])/2
            values=[float(league==code) for code in league_ids]
            for team in (match['home'],match['away']):
                for window in (5,20,50):
                    sample=teams[team][-window:];n=len(sample)
                    gf=np.array([v[0] for v in sample]);ga=np.array([v[1] for v in sample])
                    values.extend([(gf.sum()+5*mean)/(n+5),(ga.sum()+5*mean)/(n+5),
                                   (sum(3 if a>b else 1 if a==b else 0 for a,b in sample)+5)/(3*(n+5)),
                                   float((gf+ga).std()),(sum(a+b>2 for a,b in sample)+2.5)/(n+5)])
            recent=past[-40:]
            values.extend([np.mean([r['hg']+r['ag'] for r in past[-10:]]),
                           np.mean([r['hg']+r['ag'] for r in recent]),
                           np.mean([r['hg']>r['ag'] for r in recent]),
                           np.mean([r['hg']==r['ag'] for r in recent])])
            anchor=date(int(match['season'][:4]),7,1)
            phase=2*np.pi*(day-anchor).days/365.25
            values.extend([np.sin(phase),np.cos(phase)])
            output[match['id']]=values
    return output


def build_design(rows, records):
    old=design(records,history_extras(rows,records))
    new=extra_factors(rows,records)
    return np.column_stack([old,np.array([new[r['match']['id']] for r in records])])


def training_mask(records, season):
    start=min(r['match']['date'] for r in records if r['match']['season']==season)
    cutoff=(date.fromisoformat(start)-timedelta(days=2)).isoformat()
    return np.array([r['match']['season']<season and r['match']['date']<cutoff for r in records])


def learner(config):
    # Disable random holdout/early stopping: splits are entirely chronological.
    return HistGradientBoostingClassifier(max_leaf_nodes=config['leaves'], learning_rate=.05,
        max_iter=100,min_samples_leaf=80,l2_regularization=config['l2'],early_stopping=False,random_state=0)


def probabilities(outcome, goals, outcome_temp=1., goals_temp=1.):
    p=softmax(np.log(np.clip(outcome,1e-9,1))/outcome_temp,axis=1)
    over=np.clip(goals,1e-9,1-1e-9)
    over=expit(np.log(over/(1-over))/goals_temp)
    return np.column_stack([p,over,1-over])


def choose(trials, family):
    field='outcome_log_loss' if family=='outcome' else 'goals_log_loss'
    return min(trials,key=lambda t:(t['development'][field],t['id']))


def run(data, output, ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=load_matches(data);records=features(rows,50,15);x=build_design(rows,records);y=actual_array(records)
    seasons=np.array([r['match']['season'] for r in records]);train=training_mask(records,'2022-23');dev=seasons=='2022-23'
    labels=dict(outcome=y[:,:3].argmax(axis=1),goals=y[:,3].astype(int))
    trials=[]
    for group,cols in GROUPS.items():
        for leaves,l2 in ((5,20.),(7,10.),(11,5.),(15,1.),(23,2.)):
            config=dict(group=group,leaves=leaves,l2=l2);pred={}
            for family in ('outcome','goals'):
                model=learner(config).fit(x[train][:,cols],labels[family][train])
                raw=model.predict_proba(x[dev][:,cols]);pred[family]=raw if family=='outcome' else raw[:,1]
            trial=dict(id=len(trials),config=config,development=stripped(metrics(probabilities(pred['outcome'],pred['goals']),y[dev])))
            trials.append(trial);print(json.dumps(trial),flush=True)
    chosen={family:choose(trials,family) for family in ('outcome','goals')}
    cal=seasons=='2023-24';cal_train=training_mask(records,'2023-24');cal_probs={};temperatures={};cal_trials={}
    for family in ('outcome','goals'):
        config=chosen[family]['config'];cols=GROUPS[config['group']]
        model=learner(config).fit(x[cal_train][:,cols],labels[family][cal_train])
        raw=model.predict_proba(x[cal][:,cols]);cal_probs[family]=raw if family=='outcome' else raw[:,1]
    for family in ('outcome','goals'):
        field='outcome_log_loss' if family=='outcome' else 'goals_log_loss';cal_trials[family]=[]
        for temp in (.75,.85,1.,1.15,1.3,1.5):
            p=probabilities(cal_probs['outcome'],cal_probs['goals'],temp if family=='outcome' else 1.,temp if family=='goals' else 1.)
            cal_trials[family].append(dict(temperature=temp,metrics=stripped(metrics(p,y[cal]))))
        temperatures[family]=min(cal_trials[family],key=lambda t:t['metrics'][field])['temperature']
    lock=dict(protocol='factor-search-v1',created_at=datetime.now(timezone.utc).isoformat(),chosen=chosen,temperatures=temperatures,
        sklearn_version=sklearn.__version__,source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),development='2022-23',calibration='2023-24',
        audit_status='2024/25 and 2025/26 already viewed. Descriptive research, not an independent test.',
        factors=['Existing strength, venue, opponent, Elo, rest, form and historical goal features',
                 'League identity', 'Each team scoring/conceding, points, goal variation and over-2.5 frequencies over previous 5/20/50 games',
                 'League last-10/40 total goals, home-win and draw rates','Season calendar phase'],
        groups=GROUPS,features=84,candidates=len(trials),no_external_data=True)
    (out/'factor-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    audit=np.isin(seasons,['2024-25','2025-26']);audit_train=training_mask(records,'2024-25');raw={}
    for family in ('outcome','goals'):
        config=chosen[family]['config'];cols=GROUPS[config['group']]
        model=learner(config).fit(x[audit_train][:,cols],labels[family][audit_train])
        p=model.predict_proba(x[audit][:,cols]);raw[family]=p if family=='outcome' else p[:,1]
    p=probabilities(raw['outcome'],raw['goals'],temperatures['outcome'],temperatures['goals']);truth=y[audit]
    audit_records=[r for r,use in zip(records,audit) if use]
    cfg=dict(group='snaga',window=50,half_life=15,ridge=.01,rho=-.1,temperature=1.)
    base=fit(records_before(records,'2024-25'),cfg)
    reference=probability_array(intensities(audit_records,base),-.1,1.)
    # The previous specialist's frozen predictions are matched by ID, not row position.
    previous_path=Path('data/experiments/20261029-market-specialists-v1/specialists-predictions.jsonl')
    if previous_path.exists(): lines=previous_path.read_text().splitlines()
    else:
        import gzip
        lines=gzip.decompress(previous_path.with_suffix('.jsonl.gz').read_bytes()).decode().splitlines()
    previous={r['id']:r for r in (json.loads(line) for line in lines)}
    prior_indices=[i for i,r in enumerate(audit_records) if r['match']['id'] in previous]
    prior=np.array([[previous[audit_records[i]['match']['id']]['prob'][m] for m in MARKETS] for i in prior_indices])
    prior_truth=truth[prior_indices]
    print(json.dumps({'previous_specialists_overlap':len(prior_indices),'audit_total':len(audit_records),'missing_previous':len(audit_records)-len(prior_indices)}),flush=True)
    report=dict(protocol=lock,trials=trials,calibration_trials=cal_trials,audit=stripped(metrics(p,truth)),
                reference=stripped(metrics(reference,truth)),previous_specialists=stripped(metrics(prior,prior_truth)) if prior_indices else None,
                raw_audit=stripped(metrics(probabilities(raw['outcome'],raw['goals']),truth)),calibration=metrics(p,truth)['calibration'],
                previous_specialists_coverage=dict(overlap=len(prior_indices),missing=len(audit_records)-len(prior_indices)),
                by_league={},by_season={},limitations=[
                    'No new independent evidence: all development/calibration/audit seasons previously explored.',
                    'Feature ablations measured on development; they show predictive association, not causal influence.',
                    'No post-match statistics of target fixture used; strict result-release embargo of two days is an assumption.',
                    'No injury, lineup, tactical, player, xG, odds or weather data imported.',
                    'No live recommendations, no guaranteed accuracy, no profit claim.'])
    for league,name in LEAGUES.items():
        mask=np.array([r['match']['league']==league for r in audit_records]);report['by_league'][league]=dict(name=name,metrics=stripped(metrics(p[mask],truth[mask])))
    for season in ('2024-25','2025-26'):
        mask=seasons[audit]==season;report['by_season'][season]=stripped(metrics(p[mask],truth[mask]))
    (out/'factor-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if ui: Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    with (out/'factor-predictions.jsonl').open('x') as stream:
        for r,prob,actual in zip(audit_records,p,truth):
            stream.write(json.dumps(dict(id=r['match']['id'],date=r['match']['date'],prob=dict(zip(MARKETS,prob.tolist())),actual=dict(zip(MARKETS,actual.tolist()))))+'\n')
    print(json.dumps(dict(audit=report['audit'],previous_specialists=report['previous_specialists'])),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='data/openfootball');parser.add_argument('--output',required=True);parser.add_argument('--ui');args=parser.parse_args()
    run(args.data,args.output,args.ui)
