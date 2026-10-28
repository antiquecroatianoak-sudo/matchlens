"""Historical daily selections, including fixtures with unknown outcomes in the pool.
No historical odds are inferred; this never emits verified/live recommendations.
"""
import argparse,hashlib,json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from analytics.backtest import load_matches,fulltime,LEAGUES,MARKETS
from analytics.expanded_search import features,fit,intensities,probability_array,records_before

RULES=[dict(id='all',top=None,threshold=0.),dict(id='top10',top=10,threshold=0.),dict(id='top50',top=50,threshold=0.)]+[dict(id=f'p{p}',top=None,threshold=p/100) for p in (60,65,70,75,80,85,90,95)]

def all_fixtures(folder):
    played,source=load_matches(folder);known={r['id'] for r in played};pending=[]
    for path in sorted(Path(folder).glob('*.json')):
        season=path.name[:7];league=path.name[8:-5]
        if league not in LEAGUES:continue
        for item in json.loads(path.read_text())['matches']:
            if fulltime(item) is not None:continue
            if item.get('status') in ('cancelled','abandoned','postponed'):continue
            key='|'.join((league,item['date'],item['team1'],item['team2']))
            if key in known:raise ValueError('Conflicting scored and pending fixture')
            known.add(key);pending.append(dict(id=key,date=item['date'],season=season,league=league,round=item.get('round',''),home=item['team1'],away=item['team2'],hg=0,ag=0,pending=True))
    return sorted(played+pending,key=lambda r:(r['date'],r['id'])),source

def offers(records,prob):
    out=[]
    for rec,pp in zip(records,prob):
        m=rec['match'];h,a=m['hg'],m['ag'];actual=[h>a,h==a,h<a,h+a>2.5,h+a<2.5]
        for market,p,hit in zip(MARKETS,pp,actual):
            out.append(dict(id=m['id']+'|'+market,match_id=m['id'],date=m['date'],season=m['season'],league=m['league'],market=market,prob=float(p),actual=None if m.get('pending') else int(hit),history_end=rec['history_end']))
    return out

def select(pool,rule):
    days=defaultdict(list)
    for row in pool:
        if row['prob']>=rule['threshold']:days[row['date']].append(row)
    out=[]
    for day in sorted(days):
        ranked=sorted(days[day],key=lambda r:(-r['prob'],r['id']))
        out.extend(ranked if rule['top'] is None else ranked[:rule['top']])
    return out

def wilson(hits,n):
    if not n:return None
    p=hits/n;z=1.959963984540054;den=1+z*z/n;c=(p+z*z/(2*n))/den
    half=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return [max(0,c-half),min(1,c+half)]

def summary(chosen,pool):
    scored=[r for r in chosen if r['actual'] is not None];hits=sum(r['actual'] for r in scored);n=len(scored)
    available_matches={r['match_id'] for r in pool};selected_matches={r['match_id'] for r in chosen}
    return dict(selected=len(chosen),scored=n,unscored=len(chosen)-n,hits=hits,misses=n-hits,hit_rate=hits/n if n else None,mean_probability=sum(r['prob'] for r in scored)/n if n else None,offer_coverage=len(chosen)/len(pool) if pool else 0.,match_coverage=len(selected_matches)/len(available_matches) if available_matches else 0.,unique_matches=len(selected_matches),days=len({r['date'] for r in chosen}),wilson95=wilson(hits,n))

def analyze(pool):
    report=[]
    for rule in RULES:
        chosen=select(pool,rule)
        report.append(dict(rule=rule,**summary(chosen,pool),by_market={k:summary([r for r in chosen if r['market']==k],[r for r in pool if r['market']==k]) for k in MARKETS},by_season={s:summary([r for r in chosen if r['season']==s],[r for r in pool if r['season']==s]) for s in sorted({r['season'] for r in pool})}))
    return report

def run(data,source_lock,output,ui):
    out=Path(output)
    if (out/'filter-report.json').exists():raise FileExistsError('Use a new experiment directory')
    out.mkdir(parents=True,exist_ok=True)
    rows,source=all_fixtures(data);lock=json.loads(Path(source_lock).read_text());cfg=lock['selected_config'];rec=features(rows,cfg['window'],cfg['half_life'])
    # Declare every displayed selection rule before evaluating target-period outcomes.
    protocol=dict(version='daily-filters-v1',generated_at=datetime.now(timezone.utc).isoformat(),config=cfg,rules=RULES,day_timezone='Source calendar date; no kickoff times',tie_break='probability descending, stable offer id ascending',top_k_scope='All five supported markets from all ten leagues in each source calendar day; multiple offers per fixture allowed',data_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),audit_status='Descriptive reanalysis of already viewed 2024/25 and 2025/26',odds_2_plus='Unavailable: no timestamped historical odds')
    (out/'filter-lock.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
    past=[r for r in records_before(rec,'2024-25') if not r['match'].get('pending')];model=fit(past,cfg)
    targets=[r for r in rec if r['match']['season'] in ('2024-25','2025-26')]
    pp=probability_array(intensities(targets,model),cfg['rho'],cfg['temperature']);pool=offers(targets,pp)
    for r in pool:
        if not r['history_end']<r['date']:raise AssertionError('History leak')
    with (out/'filter-offers.jsonl').open('w') as f:
        for r in pool:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    report=dict(protocol=protocol,dataset_matches=sum(not r.get('pending') for r in rows),target_fixtures=sum(r['season'] in ('2024-25','2025-26') for r in rows),eligible_fixtures=len(targets),skipped_fixtures=sum(r['season'] in ('2024-25','2025-26') for r in rows)-len(targets),pool_offers=len(pool),pool_unscored=sum(r['actual'] is None for r in pool),analysis=analyze(pool),by_league={code:dict(name=name,analysis=analyze([r for r in pool if r['league']==code])) for code,name in LEAGUES.items()},limitations=['Already viewed seasons; no independent accuracy claim.','Fixture list is a retrospective snapshot, not an archived pre-kickoff schedule. Missing fixtures can change daily ranks.','Unknown outcomes remain in the ranking pool and are counted as unscored, never as losses or 0:0.','Day precision only; no reconstruction of odds or exact kickoff times.','Multiple offers from the same fixture are dependent. Wilson intervals are descriptive and assume independence; do not use them as proof.','Probability thresholds filter a fixed model; a higher selected hit rate is not a better model for all fixtures.','No live recommendations, odds 2+ test, ROI, lineups, weather or tactical inputs.'])
    (out/'filter-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    Path(ui).write_text(json.dumps({k:v for k,v in report.items() if k!='by_league'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([dict(id=x['rule']['id'],selected=x['selected'],scored=x['scored'],hit_rate=x['hit_rate'],coverage=x['match_coverage']) for x in report['analysis']],ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--source-lock',default='data/experiments/20261028-expanded-v1/expanded-lock.json');p.add_argument('--output',default='data/experiments/20261028-daily-filters-v1');p.add_argument('--ui',default='app/filter-summary.json');a=p.parse_args();run(a.data,a.source_lock,a.output,a.ui)
