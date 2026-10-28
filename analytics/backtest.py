"""Reproducible chronological research baseline. Does not publish live tips.
Dates are day-precision: a conservative two-day embargo excludes recent results.
Tuning, calibration and final test periods are fixed before evaluating candidates.
"""
import argparse, hashlib, itertools, json, math
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

MARKETS=['home','draw','away','over2.5','under2.5']
LEAGUES={'en.1':'Engleska','it.1':'Italija','es.1':'Španjolska','de.1':'Njemačka','fr.1':'Francuska','pt.1':'Portugal','be.1':'Belgija','nl.1':'Nizozemska','tr.1':'Turska','gr.1':'Grčka'}
CONFIGS=[dict(window=w,half_life=d,prior=p) for w in (10,20,50) for d in (5,10,30) for p in (4,8,16)]
SPLITS={'warmup':['2019-20','2020-21','2021-22'],'tuning':['2022-23'],'calibration':['2023-24'],'test':['2024-25','2025-26']}

def fulltime(item):
    score=item.get("score",{})
    return score.get("ft") if isinstance(score,dict) else score if isinstance(score,list) else None

def load_matches(folder):
    rows=[];manifest=[];seen=set();quality=[]
    for path in sorted(Path(folder).glob('*.json')):
        raw=path.read_bytes();season=path.name[:7];league=path.name[8:-5];dataset=json.loads(raw)
        if league not in LEAGUES:continue
        scored=sum(bool(fulltime(m)) for m in dataset['matches'])
        quality.append(dict(league=league,season=season,listed=len(dataset['matches']),scored=scored,missing_results=len(dataset['matches'])-scored))
        manifest.append(dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),url=f'https://github.com/openfootball/football.json/blob/master/{season}/{league}.json',supplemental_source=dataset.get('supplemental_source'),transformed=bool(dataset.get('supplemental_source'))))
        for item in dataset['matches']:
            score=fulltime(item)
            if not score or len(score)!=2 or not all(type(n) is int and n>=0 for n in score):continue
            day=date.fromisoformat(item['date']);home=item['team1'];away=item['team2']
            if home==away:raise ValueError('Identical teams')
            key=(league,day.isoformat(),home,away)
            if key in seen:raise ValueError('Duplicate match')
            seen.add(key)
            rows.append(dict(id='|'.join(key),date=day.isoformat(),season=season,league=league,round=item.get('round',''),home=home,away=away,hg=score[0],ag=score[1]))
    return sorted(rows,key=lambda r:(r['date'],r['id'])),dict(files=manifest,coverage=quality)

def outcomes(h,a):
    out={'home':h>a,'draw':h==a,'away':h<a,'btts':h>0 and a>0,'no_btts':not(h>0 and a>0)}
    for line in (1.5,2.5,3.5):out['over'+str(line)]=h+a>line;out['under'+str(line)]=h+a<line
    return {k:int(out[k]) for k in MARKETS}

def probabilities(lh,la):
    def pois(l):
        ps=[math.exp(-l)]
        for k in range(1,30):ps.append(ps[-1]*l/k)
        return ps
    p,q=pois(lh),pois(la);draw=sum(a*b for a,b in zip(p,q));home=0;cum=0
    for i in range(len(p)):
        home+=p[i]*cum;cum+=q[i]
    away=max(0,1-home-draw);total=home+away+draw
    over=1-math.exp(-lh-la)*(1+lh+la+(lh+la)**2/2)
    return dict(home=home/total,draw=draw/total,away=away/total,**{'over2.5':over,'under2.5':1-over})

def predict(history,match,config):
    # Past league rates only, smoothing prevents unstable estimates for newcomers.
    league=[r for r in history if (date.fromisoformat(match['date'])-date.fromisoformat(r['date'])).days<=730][-760:]
    if len(league)<100:return None
    home_base=sum(r['hg'] for r in league)/len(league);away_base=sum(r['ag'] for r in league)/len(league)
    mean=(home_base+away_base)/2
    if config is None:return probabilities(home_base,away_base)
    def stats(team):
        rs=[r for r in history if team in (r['home'],r['away'])][-config['window']:]
        if len(rs)<5:return None
        weights=[2**(-i/config['half_life']) for i in reversed(range(len(rs)))];prior=config['prior']
        scored=sum(w*(r['hg'] if r['home']==team else r['ag']) for w,r in zip(weights,rs))
        conceded=sum(w*(r['ag'] if r['home']==team else r['hg']) for w,r in zip(weights,rs))
        den=sum(weights)+prior
        return ((scored+prior*mean)/den,(conceded+prior*mean)/den)
    hs,aws=stats(match['home']),stats(match['away'])
    if hs is None or aws is None:return None
    lh=home_base*(hs[0]/mean)*(aws[1]/mean);la=away_base*(aws[0]/mean)*(hs[1]/mean)
    return probabilities(min(6,max(.15,lh)),min(6,max(.15,la)))

_CACHE={}
def contexts(rows):
    key=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    if key in _CACHE:return _CACHE[key]
    groups=defaultdict(list);result={}
    for r in rows:groups[r['league']].append(r)
    for rs in groups.values():
        history=[];teams=defaultdict(list);cursor=0
        for match in rs:
            cutoff=(date.fromisoformat(match['date'])-timedelta(days=2)).isoformat()
            while cursor<len(rs) and rs[cursor]['date']<cutoff:
                r=rs[cursor];history.append(r)
                teams[r['home']].append((r['hg'],r['ag']));teams[r['away']].append((r['ag'],r['hg']));cursor+=1
            minimum=(date.fromisoformat(match['date'])-timedelta(days=730)).isoformat()
            league=[r for r in history[-760:] if r['date']>=minimum]
            if len(league)<100:continue
            result[match['id']]=(sum(r['hg'] for r in league)/len(league),sum(r['ag'] for r in league)/len(league),list(teams[match['home']][-50:]),list(teams[match['away']][-50:]),history[-1]['date'])
    _CACHE.clear();_CACHE[key]=result;return result

def walk(rows,config,seasons=None):
    ctx=contexts(rows);result=[]
    for match in rows:
        if seasons and match['season'] not in seasons:continue
        context=ctx.get(match['id'])
        if context is None:continue
        home,away,hs,aws,end=context;mean=(home+away)/2
        if config is not None:
            if len(hs)<5 or len(aws)<5:continue
            def stats(values):
                vals=values[-config['window']:];ws=[2**(-i/config['half_life']) for i in reversed(range(len(vals)))];prior=config['prior'];den=sum(ws)+prior
                return ((sum(w*v[0] for w,v in zip(ws,vals))+prior*mean)/den,(sum(w*v[1] for w,v in zip(ws,vals))+prior*mean)/den)
            h,a=stats(hs),stats(aws);home,away=home*h[0]*a[1]/mean**2,away*a[0]*h[1]/mean**2
        p=probabilities(min(6,max(.15,home)),min(6,max(.15,away)))
        result.append(dict(id=match['id'],date=match['date'],season=match['season'],league=match['league'],round=match['round'],prob=p,actual=outcomes(match['hg'],match['ag']),history_end=end))
    return result

def metrics(predictions):
    if not predictions:return None
    markets={}
    for k in MARKETS:
        pairs=[(r['prob'][k],r['actual'][k]) for r in predictions]
        buckets=[]
        for b in range(10):
            ps=[(p,y) for p,y in pairs if min(9,int(p*10))==b]
            if ps:buckets.append(dict(n=len(ps),prob=sum(p for p,y in ps)/len(ps),rate=sum(y for p,y in ps)/len(ps)))
        markets[k]=dict(n=len(pairs),brier=sum((p-y)**2 for p,y in pairs)/len(pairs),log_loss=-sum(y*math.log(max(1e-9,p))+(1-y)*math.log(max(1e-9,1-p)) for p,y in pairs)/len(pairs),ece=sum(b['n']*abs(b['prob']-b['rate']) for b in buckets)/len(pairs),bins=buckets)
    # Equal weights for 1X2 and goals, avoiding double-counted complements.
    score=(sum(markets[k]['brier'] for k in ('home','draw','away'))/3+markets['over2.5']['brier'])/2
    picks=[max(MARKETS,key=lambda k:r['prob'][k]) for r in predictions]
    return dict(matches=len(predictions),family_brier=score,markets=markets,top_pick_hit_rate=sum(r['actual'][k] for r,k in zip(predictions,picks))/len(predictions),top_pick_mean_probability=sum(r['prob'][k] for r,k in zip(predictions,picks))/len(predictions),outcome_hit_rate=sum(r['actual'][max(('home','draw','away'),key=lambda k:r['prob'][k])] for r in predictions)/len(predictions),goals_hit_rate=sum(r['actual']['over2.5' if r['prob']['over2.5']>=.5 else 'under2.5'] for r in predictions)/len(predictions))

def fit_calibration(rows):
    # Smoothed reliability bins; only calibration-period observations are consumed.
    table={}
    for k in MARKETS:
        table[k]={}
        for b in range(5):
            values=[(r['prob'][k],r['actual'][k]) for r in rows if min(4,int(r['prob'][k]*5))==b]
            table[k][b]=dict(n=len(values),wins=sum(y for p,y in values))
    return table

def apply_calibration(rows,table):
    out=[]
    for r in rows:
        p={}
        # Calibrate base events, then enforce complementary outcomes and 1X2 sum.
        for k in ('home','draw','away','over2.5'):
            raw=r['prob'][k];cell=table[k][min(4,int(raw*5))];p[k]=(cell['wins']+30*raw)/(cell['n']+30)
        total=sum(p[k] for k in ('home','draw','away'))
        for k in ('home','draw','away'):p[k]/=total
        p['under2.5']=1-p['over2.5'];out.append({**r,'prob':p})
    return out

def run(folder,output):
    rows,source=load_matches(folder);manifest=source['files']
    if set(r['season'] for r in rows)!=set(sum(SPLITS.values(),[])):raise ValueError('Expected seven season identifiers')
    trials=[]
    for config in CONFIGS:
        tune=walk(rows,config,SPLITS['tuning'])
        trials.append(dict(config=config,tuning=metrics(tune)))
    best=min(range(len(trials)),key=lambda i:trials[i]['tuning']['family_brier'])
    chosen=walk(rows,trials[best]['config']);cal=[r for r in chosen if r['season'] in SPLITS['calibration']]
    raw_test=[r for r in chosen if r['season'] in SPLITS['test']];table=fit_calibration(cal);test=apply_calibration(raw_test,table)
    ids={r['id'] for r in raw_test};baseline=[r for r in walk(rows,None) if r['id'] in ids]
    report=dict(schema_version=2,generated_at=datetime.now(timezone.utc).isoformat(),status='research_only',source='OpenFootball / CC0',source_files=manifest,coverage=source['coverage'],dataset_matches=len(rows),leagues=LEAGUES,splits=SPLITS,embargo_days=2,selection_metric='equal-family Brier; lower is better',trials=trials,configurations_tested=len(CONFIGS),selected_config=trials[best]['config'],calibration_matches=len(cal),final_test=metrics(test),raw_final_test=metrics(raw_test),baseline_final_test=metrics(baseline),by_season={s:metrics([r for r in test if r['season']==s]) for s in SPLITS['test']},by_league={code:dict(name=name,calibrated=metrics([r for r in test if r['league']==code]),raw=metrics([r for r in raw_test if r['league']==code]),baseline=metrics([r for r in baseline if r['league']==code]),tuning_matches=sum(r['season'] in SPLITS['tuning'] and r['league']==code for r in chosen),calibration_matches=sum(r['league']==code for r in cal)) for code,name in LEAGUES.items()},by_round={code:{round_:metrics([r for r in test if r['league']==code and r['season']+' / '+r['round']==round_]) for round_ in sorted(set(r['season']+' / '+r['round'] for r in test if r['league']==code))} for code in LEAGUES},limitations=['Retrospective data snapshot, not archived as-of publication times. Two-day result-availability assumption.','Ten leagues, available full-time scores only: no lineups, tactics, injuries, weather or odds.', '2025/26 source snapshots have missing final scores: partial test, not complete final-round evidence.', 'Belgium, Turkey and Greece have missing 2021-23 source files; global configuration learned from other leagues. Calibration coverage varies.', 'Current top-ten league selection is retrospective, not a historically fixed universe.','No ROI or odds-2+ evaluation without historical executable odds.','Candidate and calibration method fixed before final test; do not retune on this test.','Probabilities require further independent prospective verification; no live tips enabled.','High-probability market selection can favor easy low-odds outcomes; hit rate alone is not evidence of advantage.'])
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    (out/'backtest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in test))
    print(json.dumps({k:report[k] for k in ('dataset_matches','selected_config','calibration_matches')}))
    print(json.dumps({k:report[k]['family_brier'] for k in ('final_test','raw_final_test','baseline_final_test')}))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--output',default='data/reports');a=p.parse_args();run(a.data,a.output)
