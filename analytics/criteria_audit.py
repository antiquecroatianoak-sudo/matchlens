"""New user criteria from prior results; unknown external facts stay unknown."""
import argparse,hashlib,itertools,json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np
from analytics.backtest import LEAGUES,MARKETS
from analytics.filter_audit import all_fixtures,summary
from analytics.active_strategy import predict_active

RULES=[dict(id=f'{profile}-{int(p*100)}',profile=profile,threshold=p)
       for profile,p in itertools.product(('all','form5','form10','venue10','streak2','h2h3'),(0.,.7,.8))]


def result(a,b):return 1 if a>b else -1 if a<b else 0


def streak(values):
    if not values:return None
    kind=values[-1]['result'];n=0
    for v in reversed(values):
        if v['result']!=kind:break
        n+=1
    return dict(result=kind,length=n)


def prior_criteria(rows):
    teams=defaultdict(list);h2h=defaultdict(list);cursor=0;out={}
    ordered=sorted(rows,key=lambda r:(r['date'],r['id']))
    for m in ordered:
        cutoff=(date.fromisoformat(m['date'])-timedelta(days=2)).isoformat()
        while cursor<len(ordered) and ordered[cursor]['date']<cutoff:
            old=ordered[cursor];cursor+=1
            if old.get('pending'):continue
            for side,opp,venue in (('home','away',True),('away','home',False)):
                gf=old['hg'] if side=='home' else old['ag'];ga=old['ag'] if side=='home' else old['hg']
                teams[(old['league'],old[side])].append(dict(gf=gf,ga=ga,home=venue,result=result(gf,ga)))
            h2h[(old['league'],tuple(sorted((old['home'],old['away']))))].append(old)
        values={}
        for side in ('home','away'):
            hist=teams[(m['league'],m[side])];v=dict(streak=streak(hist))
            for window in (5,10):
                sample=hist[-window:];v[f'n{window}']=len(sample)
                v[f'points{window}']=sum(3 if x['result']==1 else 1 if x['result']==0 else 0 for x in sample)/len(sample) if len(sample)>=window else None
                v[f'total{window}']=sum(x['gf']+x['ga'] for x in sample)/len(sample) if len(sample)>=window else None
            venue=[x for x in hist if x['home']==(side=='home')][-10:]
            v['venue_n']=len(venue)
            v['venue_gf']=sum(x['gf'] for x in venue)/len(venue) if len(venue)>=3 else None
            v['venue_ga']=sum(x['ga'] for x in venue)/len(venue) if len(venue)>=3 else None
            values[side]=v
        hh=h2h[(m['league'],tuple(sorted((m['home'],m['away']))))][-5:]
        values['h2h_n']=len(hh)
        values['h2h_diff']=sum((x['hg']-x['ag'])*(1 if x['home']==m['home'] else -1) for x in hh)/(len(hh)+8) if len(hh)>=3 else None
        values['h2h_total']=sum(x['hg']+x['ag'] for x in hh)/len(hh) if len(hh)>=3 else None
        values['h2h_draw']=sum(x['hg']==x['ag'] for x in hh)/len(hh) if len(hh)>=3 else None
        out[m['id']]=values
    return out


def aligned(col,diff,total,draw=None):
    if col==0:return diff is not None and diff>=.2
    if col==2:return diff is not None and diff<=-.2
    if col==1:return (draw>=.4 if draw is not None else abs(diff)<=.2) if diff is not None else False
    return total is not None and (total>=2.6 if col==3 else total<=2.4)


def accepts(row,rule):
    if row['prob']<rule['threshold']:return False
    profile=rule['profile'];col=row['col'];v=row['criteria'];h,a=v['home'],v['away']
    if profile=='all':return True
    if profile in ('form5','form10'):
        window=profile[4:];hp,ap=h['points'+window],a['points'+window]
        if hp is None or ap is None:return False
        return aligned(col,hp-ap,(h['total'+window]+a['total'+window])/2)
    if profile=='venue10':
        if h['venue_gf'] is None or a['venue_gf'] is None:return False
        hg=(h['venue_gf']+a['venue_ga'])/2;ag=(a['venue_gf']+h['venue_ga'])/2
        return aligned(col,hg-ag,hg+ag)
    if profile=='streak2':
        hs,aws=h['streak'],a['streak']
        if hs is None or aws is None:return False
        if col==0:return hs['result']==1 and hs['length']>=2 and aws['result']!=1
        if col==2:return aws['result']==1 and aws['length']>=2 and hs['result']!=1
        if col==1:return hs['result']==aws['result']==0 and min(hs['length'],aws['length'])>=2
        return False
    if profile=='h2h3':return aligned(col,v['h2h_diff'],v['h2h_total'],v['h2h_draw'])
    raise ValueError('Unknown criteria profile')


def make_pool(matches,probs,criteria):
    pool=[]
    for m,p in zip(matches,probs):
        col=int(np.argmax(p));h,a=m['hg'],m['ag'];truth=[h>a,h==a,h<a,h+a>2,h+a<3]
        pool.append(dict(id=m['id']+'|'+MARKETS[col],match_id=m['id'],date=m['date'],league=m['league'],season=m['season'],
                         market=MARKETS[col],col=col,prob=float(p[col]),actual=None if m.get('pending') else int(truth[col]),criteria=criteria[m['id']]))
    return pool


def analyses(pool):
    return [dict(rule=rule,**summary([r for r in pool if accepts(r,rule)],pool)) for rule in RULES]


def league_results(pool):
    results={}
    for code in LEAGUES:
        scored=[r for r in pool if r['actual'] is not None]
        own=[r for r in scored if r['league']==code];rest=[r for r in scored if r['league']!=code]
        rate=lambda rr:sum(r['actual'] for r in rr)/len(rr) if rr else None
        results[code]=dict(name=LEAGUES[code],matches=len(own),accuracy=rate(own),rest_accuracy=rate(rest),
                           deficit=(rate(rest)-rate(own)) if own else None)
    return results


def choose_exclusion(development):
    eligible=[]
    for code in LEAGUES:
        rows=[development[s][code] for s in ('2022-23','2023-24')]
        if all(r['matches']>=100 and r['deficit']>=.05 for r in rows):
            eligible.append((sum(r['deficit'] for r in rows)/2,code))
    return max(eligible)[1] if eligible else None


def run(data,output,ui,cache=None):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data);criteria=prior_criteria(rows);dev={};league_dev={}
    cached=json.loads(Path(cache).read_text()) if cache else {}
    # Optional local cache is produced in this session by predict_active; canonical IDs must match source.
    lookup={m['id']:m for m in rows}
    for season in ('2022-23','2023-24'):
        if season in cached:
            matches=cached[season]['records'];p=np.array(cached[season]['prob'])
            if any(m!=lookup.get(m['id']) for m in matches):raise ValueError('Stale development fixture cache')
        else:
            records,p,_=predict_active(rows,season);matches=[r['match'] for r in records]
        pool=make_pool(matches,p,criteria);dev[season]=analyses(pool);league_dev[season]=league_results(pool)
    excluded=choose_exclusion(league_dev)
    lock=dict(name='criteria-audit-v1',rules=RULES,source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              league_exclusion_rule='At most one league: >=100 scored fixtures in EACH development season and >=5 percentage points below all other leagues in EACH season; choose largest mean deficit.',
              excluded_league=excluded,selection='No automatic 90% strategy; report every predeclared rule. Active champion unchanged.',
              missing_inputs='Injuries, absences, expected bench, motivation, complete schedule, weather/pitch, confirmed derbies, roles and tactical styles unknown.',
              historical_status='Viewed seasons and previously tuned champion; exploratory reanalysis only.')
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    audit_preds=[json.loads(line) for line in Path('data/experiments/20261029-confidence-search-v1/predictions.jsonl').read_text().splitlines()]
    matches=[lookup[r['id']] for r in audit_preds];p=np.array([r['reference'] for r in audit_preds]);pool=make_pool(matches,p,criteria)
    report=dict(protocol=lock,development=dev,development_by_league=league_dev,audit=analyses(pool),audit_by_league=league_results(pool),
                excluded_league=excluded,active_strategy='market-specialists-v1',promoted=False,
                audited_fixtures=len(pool),available_external_facts=False,
                limitation='Filters change the selected population, not model accuracy on identical fixtures. Streaks/H2H do not prove psychology or tactical causality.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'criteria-pool.jsonl').open('x') as f:
        for row in pool:f.write(json.dumps(row)+'\n')
    Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(excluded_league=excluded,audit=[dict(id=r['rule']['id'],n=r['scored'],hits=r['hits'],accuracy=r['hit_rate'],coverage=r['match_coverage']) for r in report['audit']]),indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/criteria-summary.json');p.add_argument('--cache');a=p.parse_args();run(a.data,a.output,a.ui,a.cache)
