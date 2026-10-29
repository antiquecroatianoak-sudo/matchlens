"""Development-only league and market specialization; viewed seasons remain audit.
Local coefficients use only the league's released history. Probability mixtures
shrink local estimates toward a pooled model when evidence is weak.
"""
import argparse,hashlib,json
from collections import defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
import numpy as np
from analytics.backtest import LEAGUES,MARKETS
from analytics.expanded_search import features,intensities,probability_array,actual_array,metrics,stripped
from analytics.market_specialists import chronological_predictions,training_rows,fit_recency,combine
from analytics.filter_audit import all_fixtures,offers,analyze,RULES,select

DEV=('2022-23','2023-24');AUDIT=('2024-25','2025-26');MIN_TRAIN=200;MIN_DEV=200
CANDIDATES=[dict(id=0,alpha=0.,ridge=None)]+[dict(id=i+1,alpha=a,ridge=r) for i,(r,a) in enumerate((r,a) for r in (.001,.01,.1) for a in (.25,.5,.75,1.))]

def local_predictions(records,season,config,policy,ridge,pooled):
    targets=[r for r in records if r['match']['season']==season]
    if len(targets)!=len(pooled):raise ValueError('Pooled and local rows differ')
    groups=defaultdict(list)
    for i,rec in enumerate(targets):
        m=rec['match'];day=date.fromisoformat(m['date'])
        block='season' if policy['refit']=='season' else (day.year,(day.month-1)//3)
        groups[(m['league'],block)].append(i)
    p=pooled.copy();trace=[]
    for (league,_),indices in groups.items():
        block=[targets[i] for i in indices];cutoff=min(r['match']['date'] for r in block)
        train=[r for r in training_rows(records,cutoff) if r['match']['league']==league]
        ready=len(train)>=MIN_TRAIN
        if ready:
            model=fit_recency(train,{**config,'ridge':ridge},cutoff,policy['half_life_days'])
            p[indices]=probability_array(intensities(block,model),config['rho'],config['temperature'])
        trace.append(dict(league=league,cutoff=cutoff,train_matches=len(train),training_last_date=max((r['match']['date'] for r in train),default=None),fallback_to_pooled=not ready,targets=len(indices),ridge=ridge))
    return p,targets,trace

def score_family(p,records,family):
    known=np.array([not r['match'].get('pending') for r in records])
    if not known.any():return None
    return stripped(metrics(p[known],actual_array([r for r,k in zip(records,known) if k])))

def choose(trials,n):
    # Explicit fallback before audit; smaller alpha wins an exact score tie.
    if n<MIN_DEV:return trials[0], 'insufficient_development_matches'
    eligible=[t for t in trials if t['score'] is not None]
    return min(eligible,key=lambda t:(t['score'],t['config']['alpha'],t['config']['id'])), 'development_log_loss'

def cluster_interval(rows):
    by_match=defaultdict(list)
    for r in rows:
        if r['actual'] is not None:by_match[r['match_id']].append(r['actual'])
    if not by_match:return None
    counts=np.array([len(v) for v in by_match.values()]);hits=np.array([sum(v) for v in by_match.values()]);rng=np.random.default_rng(20261029)
    samples=rng.integers(0,len(counts),size=(1000,len(counts)))
    rates=hits[samples].sum(axis=1)/counts[samples].sum(axis=1)
    return [float(x) for x in np.quantile(rates,[.025,.975])]

def filters_with_goal(pool):
    analysis=analyze(pool)
    for item in analysis:
        selected=select(pool,item['rule']);known=[r for r in selected if r['actual'] is not None]
        unique=len({r['match_id'] for r in known});interval=cluster_interval(selected)
        item['scored_unique_matches']=unique;item['match_cluster_bootstrap95']=interval
        item['historical_90_evidence']=bool(unique>=200 and interval and interval[0]>.9)
        item['independent_90_confirmed']=False
    return analysis

def run(data,source_lock,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data);base=json.loads(Path(source_lock).read_text());base=base.get('protocol',base)
    cache={};development={};selected={};trials_by_family={};development_trace={}
    for family,config in base['seed_configs'].items():
        key=(config['window'],config['half_life'])
        if key not in cache:cache[key]=features(rows,*key)
        records=cache[key];policy=base['chosen'][family]['policy'];globals_={};locals_={};recs={};development_trace[family]=[]
        for season in DEV:
            pooled,rec,trace=chronological_predictions(records,season,config,policy);globals_[season]=pooled;recs[season]=rec
            for ridge in (.001,.01,.1):
                lp,_,lt=local_predictions(records,season,config,policy,ridge,pooled);locals_[(season,ridge)]=lp;development_trace[family].extend(lt)
        field='outcome_log_loss' if family=='outcome' else 'goals_log_loss';trials_by_family[family]={};selected[family]={}
        for code in LEAGUES:
            trials=[];n=sum(sum(r['match']['league']==code and not r['match'].get('pending') for r in recs[s]) for s in DEV)
            for candidate in CANDIDATES:
                folds={}
                for season in DEV:
                    mask=np.array([r['match']['league']==code for r in recs[season]])
                    a=candidate['alpha'];pooled=globals_[season]
                    p=pooled if not a else (1-a)*pooled+a*locals_[(season,candidate['ridge'])]
                    fold=score_family(p[mask],[r for r,k in zip(recs[season],mask) if k],family)
                    if fold:folds[season]=fold
                score=float(np.mean([m[field] for m in folds.values()])) if folds else None
                trials.append(dict(config=candidate,score=score,development=folds))
            winner,reason=choose(trials,n);selected[family][code]=dict(config=winner['config'],development_matches=n,reason=reason,development_score=winner['score'])
            trials_by_family[family][code]=trials
        print(json.dumps(dict(stage='development_complete',family=family)),flush=True)
    protocol=dict(name='league-specialists-v1',created_at=datetime.now(timezone.utc).isoformat(),selection=selected,candidates=CANDIDATES,minimum_local_training=MIN_TRAIN,minimum_development=MIN_DEV,source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_lock_sha256=hashlib.sha256(Path(source_lock).read_bytes()).hexdigest(),development_seasons=DEV,audit_seasons=AUDIT,audit_status='Already inspected seasons: descriptive reanalysis, not independent evidence',goal90='Target only. At least 200 scored distinct fixtures and match-cluster bootstrap lower bound above 90% for descriptive evidence; no independent claim on viewed data.',external_person_data_included=False)
    (out/'league-lock.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
    predictions={};pooled_predictions={};audit_records=None;audit_trace={}
    for family,config in base['seed_configs'].items():
        records=cache[(config['window'],config['half_life'])];policy=base['chosen'][family]['policy'];parts=[];baseparts=[];allrecs=[];audit_trace[family]=[]
        for season in AUDIT:
            pooled,rec,trace=chronological_predictions(records,season,config,policy);local={}
            for ridge in (.001,.01,.1):
                lp,_,lt=local_predictions(records,season,config,policy,ridge,pooled);local[ridge]=lp;audit_trace[family].extend(lt)
            p=pooled.copy()
            for i,r in enumerate(rec):
                c=selected[family][r['match']['league']]['config'];a=c['alpha']
                if a:p[i]=(1-a)*pooled[i]+a*local[c['ridge']][i]
            parts.append(p);baseparts.append(pooled);allrecs.extend(rec)
        if audit_records and [r['match']['id'] for r in audit_records]!=[r['match']['id'] for r in allrecs]:raise ValueError('Different market target pools')
        audit_records=allrecs;predictions[family]=np.concatenate(parts);pooled_predictions[family]=np.concatenate(baseparts)
    p=combine(predictions['outcome'],predictions['goals']);reference=combine(pooled_predictions['outcome'],pooled_predictions['goals'])
    known=np.array([not r['match'].get('pending') for r in audit_records]);truth=actual_array([r for r,k in zip(audit_records,known) if k])
    pool=offers(audit_records,p);filter_report=filters_with_goal(pool)
    by_league={}
    for code,name in LEAGUES.items():
        use=np.array([r['match']['league']==code for r,k in zip(audit_records,known) if k])
        by_league[code]=dict(name=name,candidate=stripped(metrics(p[known][use],truth[use])),pooled=stripped(metrics(reference[known][use],truth[use])),outcome=selected['outcome'][code],goals=selected['goals'][code])
    report=dict(protocol=protocol,configurations_per_league_market=len(CANDIDATES),selection_slots=len(LEAGUES)*2,development_comparisons=len(CANDIDATES)*len(LEAGUES)*2,trials=trials_by_family,development_training_trace=development_trace,audit_training_trace=audit_trace,audit=stripped(metrics(p[known],truth)),pooled=stripped(metrics(reference[known],truth)),by_league=by_league,by_season={s:dict(candidate=score_family(p[np.array([r['match']['season']==s for r in audit_records])],[r for r in audit_records if r['match']['season']==s],'all'),pooled=score_family(reference[np.array([r['match']['season']==s for r in audit_records])],[r for r in audit_records if r['match']['season']==s],'all')) for s in AUDIT},filters=filter_report,eligible_fixtures=len(audit_records),unscored_fixtures=int((~known).sum()),limitations=['League-local coefficients, local/global blend and shrinkage selected only on earlier development outcomes.','If local training <200 fixtures, local predictions fall back to pooled; if development <200, league selection stays pooled.','Viewed audit periods cannot certify future 90% accuracy, regardless of number of repeated trials.','Probability filters select subsets; report hits, misses, unscored, unique fixtures and coverage.','Coach and direct player-pair features still unavailable; not used or inferred from club results.','Lineups, odds, tactical events and injury data absent. Calendar-date schedule is a retrospective snapshot.','Match-cluster interval handles offers sharing a fixture, but not all temporal/league dependence or model-selection uncertainty.'])
    (out/'league-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/'league-offers.jsonl').open('x') as stream:
        for r in pool:stream.write(json.dumps(r,ensure_ascii=False)+'\n')
    compact={k:v for k,v in report.items() if k not in ('trials','development_training_trace','audit_training_trace')};Path(ui).write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(audit=report['audit'],pooled=report['pooled'],selected=selected,filters=[dict(id=r['rule']['id'],hits=r['hits'],misses=r['misses'],scored=r['scored'],unique=r['scored_unique_matches'],rate=r['hit_rate'],historical_90_evidence=r['historical_90_evidence']) for r in filter_report]),ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--source-lock',default='data/experiments/20261029-market-specialists-v1/specialists-lock.json');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/league-summary.json');a=p.parse_args();run(a.data,a.source_lock,a.output,a.ui)
