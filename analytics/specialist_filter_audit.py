"""Apply unchanged daily filter rules to the newer market-specific candidate.
No threshold tuning on viewed audit results. Unknown outcomes remain ranked.
"""
import argparse,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from analytics.filter_audit import all_fixtures,offers,analyze,RULES
from analytics.expanded_search import features
from analytics.market_specialists import chronological_predictions,combine
from analytics.backtest import LEAGUES

def run(data,lock_path,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data);lock=json.loads(Path(lock_path).read_text());protocol=lock['protocol'] if 'protocol' in lock else lock
    plan=dict(version='specialist-daily-filters-v1',generated_at=datetime.now(timezone.utc).isoformat(),source_model='market-specialists-v1',source_lock_sha256=hashlib.sha256(Path(lock_path).read_bytes()).hexdigest(),rules=RULES,day_timezone='Source calendar date; no kickoff times',audit_status='Previously viewed 2024/25 and 2025/26; descriptive comparison only',top_k_scope='All five markets, all ten leagues, multiple offers per fixture',odds_2_plus='Not evaluated: no historical timestamped odds',source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest())
    (out/'filter-lock.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    cache={};families={};common=None;targets=None
    for family,config in protocol['seed_configs'].items():
        key=(config['window'],config['half_life']);cache.setdefault(key,features(rows,*key))
        parts=[];records=[]
        for season in ('2024-25','2025-26'):
            p,rec,trace=chronological_predictions(cache[key],season,config,protocol['chosen'][family]['policy']);parts.append(p);records.extend(rec)
        ids=[r['match']['id'] for r in records]
        if common is not None and common!=ids:raise ValueError('Differing candidate pools')
        common=ids;targets=records;families[family]=np.concatenate(parts)
    pool=offers(targets,combine(families['outcome'],families['goals']))
    with (out/'filter-offers.jsonl').open('x') as stream:
        for row in pool:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    previous=json.loads(Path('data/experiments/20261028-daily-filters-v1/filter-report.json').read_text())
    report=dict(protocol=plan,dataset_matches=sum(not r.get('pending') for r in rows),target_fixtures=sum(r['season'] in ('2024-25','2025-26') for r in rows),eligible_fixtures=len(targets),skipped_fixtures=sum(r['season'] in ('2024-25','2025-26') for r in rows)-len(targets),pool_offers=len(pool),pool_unscored=sum(r['actual'] is None for r in pool),analysis=analyze(pool),previous_analysis=previous['analysis'],by_league={code:dict(name=name,analysis=analyze([r for r in pool if r['league']==code])) for code,name in LEAGUES.items()},limitations=previous['limitations']+['Newer candidate uses only result-derived features. Coach and player-pair inputs not available; no claimed contribution.','Model refits follow the previously chosen season/quarter policies, using only earlier available results.'])
    (out/'filter-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    Path(ui).write_text(json.dumps({k:v for k,v in report.items() if k!='by_league'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([dict(id=r['rule']['id'],hits=r['hits'],misses=r['misses'],scored=r['scored'],unscored=r['unscored'],hit_rate=r['hit_rate']) for r in report['analysis']],ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--lock',default='data/experiments/20261029-market-specialists-v1/specialists-lock.json');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/filter-specialists-summary.json');a=p.parse_args();run(a.data,a.lock,a.output,a.ui)
