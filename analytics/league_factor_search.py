"""New local feature ablations, reusing the completed league development trials.
Does not retune on audit results or rerun the old 260 development comparisons.
"""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from analytics.backtest import LEAGUES,MARKETS
from analytics.expanded_search import GROUPS as FEATURE_GROUPS,features,actual_array,metrics,stripped
from analytics.market_specialists import chronological_predictions,combine
from analytics.filter_audit import all_fixtures,offers
from analytics.league_specialists import DEV,AUDIT,MIN_DEV,MIN_TRAIN,local_predictions,score_family,choose,filters_with_goal

NEW_GROUPS={'full_context':list(range(9)),'without_current_elo':[0,1,2,3,4,5,6,8],'attack_defence_only':[0,1]}
for name,cols in NEW_GROUPS.items():FEATURE_GROUPS[name]=cols
NEW_CANDIDATES=[dict(id=13+i,alpha=alpha,ridge=ridge,group=group) for i,(group,ridge,alpha) in enumerate((g,r,a) for g in NEW_GROUPS for r in (.001,.01,.1) for a in (.25,.5,.75,1.))]

def load_offers(path,records):
    by_match={}
    for line in Path(path).read_text().splitlines():
        r=json.loads(line);by_match.setdefault(r['match_id'],{})[r['market']]=r['prob']
    return np.array([[by_match[r['match']['id']][k] for k in MARKETS] for r in records])

def run(data,source_lock,previous,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data);previous=Path(previous);prior=json.loads((previous/'league-report.json').read_text())
    fingerprint=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
    if fingerprint!=prior['protocol']['source_sha256']:raise ValueError('Source changed; old development scores cannot be reused')
    base=json.loads(Path(source_lock).read_text());base=base.get('protocol',base)
    cache={};trials={};selected={};trace={}
    for family,config in base['seed_configs'].items():
        key=(config['window'],config['half_life'])
        if key not in cache:cache[key]=features(rows,*key)
        recs=cache[key];policy=base['chosen'][family]['policy'];pooled={};records={};local={};trace[family]=[]
        for season in DEV:
            pooled[season],records[season],_=chronological_predictions(recs,season,config,policy)
            for group in NEW_GROUPS:
                for ridge in (.001,.01,.1):
                    p,_,t=local_predictions(recs,season,{**config,'group':group},policy,ridge,pooled[season]);local[(season,group,ridge)]=p;trace[family].extend([{**x,'group':group} for x in t])
        trials[family]={};selected[family]={};field='outcome_log_loss' if family=='outcome' else 'goals_log_loss'
        for code in LEAGUES:
            existing=[{**t,'config':{**t['config'],'group':'pooled' if t['config']['alpha']==0 else 'snaga'},'reused':True} for t in prior['trials'][family][code]]
            for candidate in NEW_CANDIDATES:
                folds={}
                for season in DEV:
                    a=candidate['alpha'];p=(1-a)*pooled[season]+a*local[(season,candidate['group'],candidate['ridge'])]
                    mask=np.array([r['match']['league']==code for r in records[season]])
                    fold=score_family(p[mask],[r for r,k in zip(records[season],mask) if k],family)
                    if fold:folds[season]=fold
                score=float(np.mean([m[field] for m in folds.values()])) if folds else None
                existing.append(dict(config=candidate,score=score,development=folds,reused=False))
            n=prior['protocol']['selection'][family][code]['development_matches'];winner,reason=choose(existing,n)
            trials[family][code]=existing;selected[family][code]=dict(config=winner['config'],development_matches=n,reason=reason,development_score=winner['score'],reused_prior_candidate=winner['reused'])
        print(json.dumps(dict(stage='new_groups_complete',family=family)),flush=True)
    protocol=dict(name='league-factor-search-v1',created_at=datetime.now(timezone.utc).isoformat(),selection=selected,new_groups=NEW_GROUPS,new_candidates=NEW_CANDIDATES,source_sha256=fingerprint,previous_report_sha256=hashlib.sha256((previous/'league-report.json').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),development_seasons=DEV,audit_seasons=AUDIT,minimum_local_training=MIN_TRAIN,minimum_development=MIN_DEV,audit_status='Already viewed seasons; descriptive reanalysis only',external_person_data_included=False,goal90=prior['protocol']['goal90'])
    (out/'league-lock.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
    families={};reference=None;targets=None;audit_trace={}
    for family,config in base['seed_configs'].items():
        recs=cache[(config['window'],config['half_life'])];policy=base['chosen'][family]['policy'];all_records=[];all_parts=[];audit_trace[family]=[]
        for season in AUDIT:
            pooled,records,_=chronological_predictions(recs,season,config,policy)
            old=load_offers(previous/'league-offers.jsonl',records);p=old.copy();needed={(s['config']['group'],s['config']['ridge']) for s in selected[family].values() if not s['reused_prior_candidate']}
            local={}
            for group,ridge in needed:
                lp,_,lt=local_predictions(recs,season,{**config,'group':group},policy,ridge,pooled);local[(group,ridge)]=lp;audit_trace[family].extend([{**t,'group':group} for t in lt])
            for i,r in enumerate(records):
                s=selected[family][r['match']['league']]
                if not s['reused_prior_candidate']:
                    c=s['config'];p[i]=(1-c['alpha'])*pooled[i]+c['alpha']*local[(c['group'],c['ridge'])][i]
            all_parts.append(p);all_records.extend(records)
        if targets and [r['match']['id'] for r in targets]!=[r['match']['id'] for r in all_records]:raise ValueError('Market target pools differ')
        targets=all_records;families[family]=np.concatenate(all_parts)
    p=combine(families['outcome'],families['goals']);pooled=load_offers('data/experiments/20261029-specialist-filters-v1/filter-offers.jsonl',targets)
    old=load_offers(previous/'league-offers.jsonl',targets);known=np.array([not r['match'].get('pending') for r in targets]);y=actual_array([r for r,k in zip(targets,known) if k])
    pool=offers(targets,p);by_league={}
    for code,name in LEAGUES.items():
        use=np.array([r['match']['league']==code for r,k in zip(targets,known) if k])
        by_league[code]=dict(name=name,candidate=stripped(metrics(p[known][use],y[use])),pooled=stripped(metrics(pooled[known][use],y[use])),previous_local=stripped(metrics(old[known][use],y[use])),outcome=selected['outcome'][code],goals=selected['goals'][code])
    report=dict(protocol=protocol,configurations_per_league_market=49,selection_slots=20,development_comparisons=980,new_development_comparisons=720,reused_development_comparisons=260,trials=trials,development_training_trace=trace,audit_training_trace=audit_trace,audit=stripped(metrics(p[known],y)),pooled=stripped(metrics(pooled[known],y)),previous_local=stripped(metrics(old[known],y)),by_league=by_league,filters=filters_with_goal(pool),eligible_fixtures=len(targets),unscored_fixtures=int((~known).sum()),limitations=prior['limitations']+['720 new group-ablation comparisons plus 260 reused prior comparisons; not 980 new independent tests.','without_current_elo removes the current rating difference but retains opponent-history ratings in the context group.','Full context adds venue, previous-opponent strength, form and recorded league fixture gaps; it does not add actual tactics or personnel data.'])
    (out/'league-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/'league-offers.jsonl').open('x') as stream:
        for r in pool:stream.write(json.dumps(r,ensure_ascii=False)+'\n')
    compact={k:v for k,v in report.items() if k not in ('trials','development_training_trace','audit_training_trace')};Path(ui).write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(audit=report['audit'],pooled=report['pooled'],previous_local=report['previous_local'],selected=selected,filters=[dict(id=r['rule']['id'],scored=r['scored'],hits=r['hits'],misses=r['misses'],unique=r['scored_unique_matches'],rate=r['hit_rate'],historical_90_evidence=r['historical_90_evidence']) for r in report['filters']]),ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--data',default='data/openfootball');a.add_argument('--source-lock',default='data/experiments/20261029-market-specialists-v1/specialists-lock.json');a.add_argument('--previous',default='data/experiments/20261029-league-specialists-v1');a.add_argument('--output',required=True);a.add_argument('--ui',default='app/league-factor-summary.json');p=a.parse_args();run(p.data,p.source_lock,p.previous,p.output,p.ui)
