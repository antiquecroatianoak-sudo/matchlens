"""One unified seven-market, round-frozen quarter pilot on real source inputs.

Two sources: CC0 fixtures/results and CC-BY4 price CSV + dated ledger hashes.
Historical source snapshots and provider hash claims remain assumptions, not
independent verification of an executable market or pre-announced schedule.
"""
import argparse,csv,hashlib,json,re,unicodedata
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
from analytics.active_strategy import load_active
from analytics.filter_audit import all_fixtures,summary
from analytics.expanded_search import features,intensities,probability_array
from analytics.market_specialists import training_rows,fit_recency
from analytics.round_quarter import frozen_features,select_round
from analytics.synthetic_odds import terms
from analytics.synthetic_odds_audit import SCOPE
from analytics.backtest import MARKETS,LEAGUES

PILOT_CODES={'en.1','it.1','es.1','de.1','fr.1','pt.1','nl.1'}
START='2026-08-07';END='2026-09-25'
NAMES=MARKETS+['1X','X2']


def norm(name):
    value=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()
    tokens=re.findall('[a-z0-9]+',value)
    ignored={'fc','cf','afc','sc','sv','ac','as','ss','us','ud','cd','rc','gd','sl','club','calcio','football','1'}
    return ''.join(t for t in tokens if t not in ignored and not (len(t)==4 and t.isdigit()))


def source_inputs():
    old,old_source=all_fixtures('data/openfootball');new,new_source=all_fixtures('data/pilot-2026/results')
    rows=sorted(old+new,key=lambda r:(r['date'],r['id']))
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate history fixture')
    lookup=defaultdict(list)
    for r in new:lookup[(r['league'],r['date'],norm(r['home']),norm(r['away']))].append(r)
    raw_times={}
    for f in Path('data/pilot-2026/results').glob('*.json'):
        league=f.name[8:-5]
        for m in json.loads(f.read_text())['matches']:
            key='|'.join((league,m['date'],m['team1'],m['team2']))
            raw_times[key]=m.get('time','00:00')
    csv_rows={r['id']:r for r in csv.DictReader(Path('data/odds/tipsaudit-predictions-all.csv').open())}
    snapshots=[];qlog=Counter()
    for f in sorted(Path('data/pilot-2026').glob('checkpoint-*.json')):
        snap=json.loads(f.read_text());available=datetime.fromisoformat(snap['generated_at']);items={}
        for raw in snap['predictions']:
            csv_row=csv_rows.get(str(raw['id']))
            if not csv_row:continue
            code=SCOPE.get((csv_row['country'],csv_row['league']))
            if code not in PILOT_CODES:continue
            qlog['snapshot_candidates']+=1
            if raw.get('hash')!=csv_row['record_hash']:qlog['changed_hash']+=1;continue
            if raw.get('settled') or raw.get('result') is not None:qlog['already_settled']+=1;continue
            kickoff=datetime.fromisoformat(raw['kickoff_utc']);logged=datetime.fromisoformat(raw['logged_at_utc'])
            if logged.date().isoformat()<'2026-07-28':logged-=timedelta(hours=3)
            if not logged<=available<kickoff:qlog['invalid_time']+=1;continue
            matches=lookup.get((code,kickoff.date().isoformat(),norm(raw['home']),norm(raw['away'])),[])
            if len(matches)!=1:qlog['unmatched_names']+=1;continue
            m=matches[0]
            if m['id'] in items:qlog['duplicate_source_prediction']+=1;continue
            try:
                prices={k:float(csv_row['pin_open_'+field]) for k,field in [('1','home'),('X','draw'),('2','away')]}
                for s in ('1X','X2'):terms(s,prices)
            except (ValueError,TypeError):qlog['invalid_prices']+=1;continue
            # Outcome used for QA only after exact identity join, never ranking.
            if not m.get('pending'):
                actual='1' if m['hg']>m['ag'] else 'X' if m['hg']==m['ag'] else '2'
                if csv_row['result'] and csv_row['result']!=actual:qlog['result_conflict']+=1
            items[m['id']]=dict(prices=prices,source_id=raw['id'],record_hash=raw['hash'],available_at=snap['generated_at'])
        snapshots.append(dict(available=available,items=items,path=snap['path'],git_blob=snap['git_blob']))
    return rows,new,raw_times,snapshots,dict(qlog),dict(old=old_source,new=new_source)


def earliest_bound(targets,raw_times):
    # All seven leagues' possible local UTC offsets are <=+03:00. Using +03
    # for every published local time is a deliberately earlier UTC lower bound.
    # Missing time -> local midnight, even more conservative. Not exact kickoff.
    bounds=[]
    for m in targets:
        raw=raw_times[m['id']]
        if not re.fullmatch(r'\d\d:\d\d',raw):raw='00:00'
        d=datetime.fromisoformat(m['date']+'T'+raw).replace(tzinfo=timezone(timedelta(hours=3)))
        bounds.append(d.astimezone(timezone.utc))
    return min(bounds)


def choose_offer(m,p,quote=None,joint=True):
    values=list(p);labels=list(MARKETS)
    if joint and quote:
        for s,prob in (('1X',p[0]+p[1]),('X2',p[1]+p[2])):
            if terms(s,quote['prices'])['odds']>=2:labels.append(s);values.append(float(prob))
    col=max(range(len(values)),key=lambda i:(values[i],-i));label=labels[col]
    h,a=m['hg'],m['ag'];actual=[h>a,h==a,h<a,h+a>2,h+a<3,h>=a,a>=h]
    ix=(list(MARKETS)+['1X','X2']).index(label)
    return dict(id=m['id']+'|'+label,match_id=m['id'],date=m['date'],league=m['league'],season=m['season'],
                round=m['round'],market=label,prob=float(values[col]),margin=0.,
                actual=None if m.get('pending') else int(actual[ix]),
                synthetic_odds=terms(label,quote['prices'])['odds'] if label in ('1X','X2') else None)


def run(output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,new,raw_times,snapshots,qa,sources=source_inputs();active=load_active();cache={};models={}
    rounds=defaultdict(list)
    for m in new:
        if m['league'] in PILOT_CODES:rounds[(m['league'],m['season'],m['round'])].append(m)
    target_rounds={k:v for k,v in rounds.items() if START<=min(m['date'] for m in v)<=END}
    for cfg in active['seed_configs'].values():
        key=(cfg['window'],cfg['half_life'])
        if key not in cache:cache[key]=features(rows,*key)
    lock=dict(name='joint-seven-quarter-pilot-v2',period=[START,END],markets=list(MARKETS)+['1X','X2'],
              policy='One best permitted offer per fixture, then floor(whole round size/4) fixtures by probability.',
              double_chance='Only user-approved synthetic same-Pinnacle raw-1X2 odds >=2; no odds inferred from model.',
              no_price_policy='1X/X2 unavailable; original five markets remain valid. Missing games remain in quota denominator.',
              model='Existing market-specialists coefficients/policies; no tuning on pilot outcomes.',
              history='All results strictly before earliest round date minus2days.',
              checkpoint_rule='Latest source checkpoint strictly before conservative first-kickoff lower bound; unchanged provider record_hash against CSV.',
              assumptions=['Provider says record_hash covers component pin_open prices; raw components are not exposed in old JSON. This coverage claim is relied upon, not independently recomputed.',
                           'Provider-generated checkpoint timestamps are not independently verified publication/Bitcoin attestation times.',
                           'Fixtures/rounds are retrospective OpenFootball snapshot. Local time +03 lower bound, not exact verified kickoff.'],
              source_sha256=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest(),
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),promote=False)
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    all_base=[];all_joint=[];chosen_base=[];chosen_joint=[];traces=[];eligible_dc=0;matched_quotes=0
    for index,(key,targets) in enumerate(sorted(target_rounds.items())):
        freeze=min(m['date'] for m in targets);bound=earliest_bound(targets,raw_times)
        eligible_snapshots=[s for s in snapshots if s['available']<bound]
        snapshot=max(eligible_snapshots,key=lambda s:s['available']) if eligible_snapshots else None
        quotes=snapshot['items'] if snapshot else {};families={};common=None;recs=None
        for family,cfg in active['seed_configs'].items():
            records=cache[(cfg['window'],cfg['half_life'])];policy=active['policies'][family]
            year,q=int(freeze[:4]),(int(freeze[5:7])-1)//3
            available=[r for r in records if r['match']['season']==key[1] and (policy['refit']=='season' or (int(r['match']['date'][:4]),(int(r['match']['date'][5:7])-1)//3)==(year,q))]
            if not available:families={};break
            cutoff=min(r['match']['date'] for r in available)
            if cutoff>freeze:families={};break
            mk=(family,cutoff)
            if mk not in models:models[mk]=fit_recency(training_rows(records,cutoff),cfg,cutoff,policy['half_life_days'])
            rr=frozen_features(rows,targets,freeze,cfg['window'],cfg['half_life'])
            if not rr:families={};break
            ids=[r['match']['id'] for r in rr]
            if common is not None and ids!=common:raise ValueError('Mismatched candidate fixture cohorts')
            common=ids;recs=rr;families[family]=probability_array(intensities(rr,models[mk]),cfg['rho'],cfg['temperature'])
        if not families:continue
        pp=np.column_stack([families['outcome'][:,:3],families['goals'][:,3:]])
        base=[];joint=[]
        for rec,p in zip(recs,pp):
            m=rec['match'];quote=quotes.get(m['id'])
            if quote:
                matched_quotes+=1;eligible_dc+=sum(terms(s,quote['prices'])['odds']>=2 for s in ('1X','X2'))
            base.append(choose_offer(m,p,joint=False));joint.append(choose_offer(m,p,quote))
        selected_b=select_round(base,len(targets),0.);selected_j=select_round(joint,len(targets),0.)
        all_base.extend(base);all_joint.extend(joint);chosen_base.extend(selected_b);chosen_joint.extend(selected_j)
        traces.append(dict(round='|'.join(key),freeze=freeze,first_start_lower_bound=bound.isoformat(),
                           checkpoint=snapshot['path'] if snapshot else None,checkpoint_time=snapshot['available'].isoformat() if snapshot else None,
                           total_fixtures=len(targets),eligible_fixtures=len(base),base=selected_b,joint=selected_j))
    total=sum(len(v) for v in target_rounds.values())
    report=dict(protocol=lock,source_fixtures=total,source_rounds=len(target_rounds),tested_rounds=len(traces),
                covered_leagues=[dict(code=c,name=LEAGUES[c]) for c in sorted(PILOT_CODES)],
                not_covered_leagues=[dict(code=c,name=LEAGUES[c]) for c in LEAGUES if c not in PILOT_CODES],
                eligible_fixtures=len(all_joint),matched_pre_round_price_snapshots=matched_quotes,
                admitted_double_chance_offers=eligible_dc,selected_double_chance=sum(r['market'] in ('1X','X2') for r in chosen_joint),
                baseline=summary(chosen_base,all_base),joint=summary(chosen_joint,all_joint),
                selected_market_counts=dict(Counter(r['market'] for r in chosen_joint)),
                selection_changed_rounds=sum([r['match_id'] for r in t['base']]!=[r['match_id'] for r in t['joint']] for t in traces),
                source_coverage=len(chosen_joint)/total if total else 0.,quality=qa,independent_90_confirmed=False,promoted=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'rounds.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in traces))
    Path(ui).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('protocol','covered_leagues','not_covered_leagues')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--ui',default='app/joint-quarter-summary.json');a=p.parse_args();run(a.output,a.ui)
