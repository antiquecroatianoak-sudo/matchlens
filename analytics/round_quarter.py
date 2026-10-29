"""Round-frozen forecasts and selection of at most 25% of source round fixtures.

All target-round results are embargoed at the earliest source round date.
Source dates/round schedules are retrospective; not an archived live backtest.
"""
import argparse,hashlib,json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np
from analytics.backtest import LEAGUES,MARKETS
from analytics.filter_audit import all_fixtures,summary
from analytics.expanded_search import features,intensities,probability_array
from analytics.market_specialists import fit_recency,training_rows
from analytics.active_strategy import load_active

LAMBDAS=(0.,-.2,-.1,.05,.1,.2,.3,.5,1.)


def frozen_features(rows,targets,freeze,window,half_life):
    cutoff=(date.fromisoformat(freeze)-timedelta(days=2)).isoformat()
    league=targets[0]['league'];past=[r for r in rows if r['league']==league and r['date']<cutoff and not r.get('pending')]
    teams=defaultdict(list);rating=defaultdict(lambda:1500.)
    for r in past:
        h,a=r['home'],r['away'];rh,ra=rating[h],rating[a]
        expected=1/(1+10**((ra-rh-60)/400));actual=1 if r['hg']>r['ag'] else .5 if r['hg']==r['ag'] else 0
        rating[h]+=20*(actual-expected);rating[a]-=20*(actual-expected)
        teams[h].append((r['hg'],r['ag'],1,ra,r['date']));teams[a].append((r['ag'],r['hg'],0,rh,r['date']))
    result=[]
    for m in targets:
        day=date.fromisoformat(m['date']);recent=[r for r in past[-760:] if (day-date.fromisoformat(r['date'])).days<=730]
        if len(recent)<100:continue
        hb=sum(r['hg'] for r in recent)/len(recent);ab=sum(r['ag'] for r in recent)/len(recent);mean=(hb+ab)/2
        if mean<=0:continue
        def stats(team,venue):
            vals=teams[team][-window:]
            if len(vals)<5:return None
            weights=np.array([2**(-i/half_life) for i in reversed(range(len(vals)))])
            def rates(v,w):
                den=sum(w)+8
                return (sum(t[0]*z for t,z in zip(v,w))+8*mean)/den,(sum(t[1]*z for t,z in zip(v,w))+8*mean)/den
            gf,ga=rates(vals,weights);same=[(v,w) for v,w in zip(vals,weights) if v[2]==venue]
            vgf,vga=rates([v for v,w in same],[w for v,w in same])
            strength=sum(w*(v[3]-1500)/400 for v,w in zip(vals,weights))/(sum(weights)+8)
            last=vals[-5:];form=sum(3 if v[0]>v[1] else 1 if v[0]==v[1] else 0 for v in last)/len(last)
            rest=min(14,max(2,(day-date.fromisoformat(vals[-1][4])).days))
            return gf,ga,vgf,vga,strength,form,rest
        h,a=stats(m['home'],1),stats(m['away'],0)
        if h is None or a is None:continue
        def vector(own,opp,rt):
            return [np.log(own[0]/mean),np.log(opp[1]/mean),np.log(own[2]/own[0]),np.log(opp[3]/opp[1]),own[4],opp[4],(own[5]-opp[5])/3,rt/400,(own[6]-opp[6])/12]
        result.append(dict(match=m,x=[vector(h,a,rating[m['home']]-rating[m['away']]),vector(a,h,rating[m['away']]-rating[m['home']])],
                           offset=[np.log(max(.1,hb)),np.log(max(.1,ab))],history_end=past[-1]['date'],freeze=freeze))
    return result


def make_pool(matches,prob,round_key,freeze):
    pool=[]
    for m,p in zip(matches,prob):
        col=int(np.argmax(p));family=p[:3] if col<3 else p[3:];ss=sorted(family,reverse=True)
        h,a=m['hg'],m['ag'];truth=[h>a,h==a,h<a,h+a>2,h+a<3]
        pool.append(dict(id=m['id']+'|'+MARKETS[col],match_id=m['id'],date=m['date'],season=m['season'],league=m['league'],
                         round=round_key,freeze=freeze,market=MARKETS[col],prob=float(p[col]),margin=float(ss[0]-ss[1]),
                         actual=None if m.get('pending') else int(truth[col])))
    return pool


def select_round(pool,total_round_fixtures,weight):
    # Budget comes from the whole source round, including unknown outcomes and
    # fixtures with no usable prediction; never count only later scored games.
    if len({r['match_id'] for r in pool})!=len(pool):raise ValueError('One best offer per fixture required')
    if total_round_fixtures<len(pool):raise ValueError('Invalid round fixture count')
    return sorted(pool,key=lambda r:(-(r['prob']+weight*r['margin']),r['match_id']))[:total_round_fixtures//4]


def run(data,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data);active=load_active();cache={};models={};rounds=defaultdict(list)
    seasons=('2022-23','2023-24','2024-25','2025-26')
    for m in rows:
        if m['season'] in seasons and m.get('round'):rounds[(m['league'],m['season'],m['round'])].append(m)
    for cfg in active['seed_configs'].values():
        key=(cfg['window'],cfg['half_life'])
        if key not in cache:cache[key]=features(rows,*key)
    def predict_round(targets):
        freeze=min(m['date'] for m in targets);parts={};common=None;records=None
        for family,cfg in active['seed_configs'].items():
            base=cache[(cfg['window'],cfg['half_life'])];policy=active['policies'][family]
            season=targets[0]['season'];year=int(freeze[:4]);quarter=(int(freeze[5:7])-1)//3
            available=[r for r in base if r['match']['season']==season and (policy['refit']=='season' or (int(r['match']['date'][:4]),(int(r['match']['date'][5:7])-1)//3)==(year,quarter))]
            if not available:return [],np.empty((0,5)),freeze
            cutoff=min(r['match']['date'] for r in available)
            if cutoff>freeze:return [],np.empty((0,5)),freeze
            key=(family,cutoff)
            if key not in models:models[key]=fit_recency(training_rows(base,cutoff),cfg,cutoff,policy['half_life_days'])
            rec=frozen_features(rows,targets,freeze,cfg['window'],cfg['half_life'])
            if not rec:return [],np.empty((0,5)),freeze
            ids=[r['match']['id'] for r in rec]
            if common is not None and ids!=common:raise ValueError('Different eligible frozen fixtures')
            common=ids;records=rec;parts[family]=probability_array(intensities(rec,models[key]),cfg['rho'],cfg['temperature'])
        return [r['match'] for r in records],np.column_stack([parts['outcome'][:,:3],parts['goals'][:,3:]]),freeze
    pools={};totals={}
    def process(season):
        for key,targets in sorted(rounds.items()):
            if key[1]!=season:continue
            match,p,freeze=predict_round(targets);rid='|'.join(key)
            pools[rid]=make_pool(match,p,rid,freeze);totals[rid]=len(targets)
        print(json.dumps(dict(completed=season,rounds=sum(key[1]==season for key in rounds))),flush=True)
    for season in seasons[:2]:process(season)
    trials=[]
    for weight in LAMBDAS:
        development={}
        for season in seasons[:2]:
            full=[r for pool in pools.values() for r in pool if r['season']==season]
            chosen=[r for rid,pool in pools.items() if rid.split('|')[1]==season for r in select_round(pool,totals[rid],weight)]
            development[season]=summary(chosen,full)
        trials.append(dict(weight=weight,development=development,score=sum(v['hit_rate'] for v in development.values())/2))
    selected=max(trials,key=lambda r:(r['score'],-abs(r['weight']),-r['weight']))['weight']
    lock=dict(name='round-quarter-v1',ratio=.25,budget='floor(source round fixture count / 4)',unit='league + season + source round',
              selected_weight=selected,trials=trials,development=list(seasons[:2]),audit=list(seasons[2:]),
              history_cutoff='Strictly before earliest round fixture date minus two days, for EVERY fixture in the round.',
              source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              limitations=['Round labels, fixtures and dates are retrospective source snapshots; historical pre-round publication not archived.',
                           'Already viewed development/audit and inherited model tuning; descriptive research, not independent future accuracy.',
                           'Only five original markets: 1X/X2 excluded because real historical quotes >=2 unavailable.'])
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    for season in seasons[2:]:process(season)
    full=[r for pool in pools.values() for r in pool if r['season'] in seasons[2:]]
    selected_rows=[r for rid,pool in pools.items() if rid.split('|')[1] in seasons[2:] for r in select_round(pool,totals[rid],selected)]
    baseline=[r for rid,pool in pools.items() if rid.split('|')[1] in seasons[2:] for r in select_round(pool,totals[rid],0.)]
    total=sum(n for rid,n in totals.items() if rid.split('|')[1] in seasons[2:])
    report=dict(protocol=lock,source_round_fixtures=total,eligible_predictions=len(full),
                all_frozen=summary(full,full),quarter=summary(selected_rows,full),confidence_quarter=summary(baseline,full),
                selected_source_coverage=len(selected_rows)/total if total else 0,
                by_league={code:dict(name=name,quarter=summary([r for r in selected_rows if r['league']==code],[r for r in full if r['league']==code])) for code,name in LEAGUES.items()},
                independent_90_confirmed=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    with (out/'selected.jsonl').open('x') as f:
        for r in selected_rows:f.write(json.dumps(r)+'\n')
    with (out/'round-pools.jsonl').open('x') as f:
        for rid,pool in pools.items():f.write(json.dumps(dict(round=rid,source_fixtures=totals[rid],pool=pool))+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('protocol','by_league')},indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/quarter-summary.json');a=p.parse_args();run(a.data,a.output,a.ui)
