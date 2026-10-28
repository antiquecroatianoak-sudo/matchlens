"""Deterministic walk-forward development search; previously viewed seasons are audit only.
No post-match statistics enter the features. numpy/scipy are used only offline.
"""
import argparse
import hashlib
import itertools
import json
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.stats import skellam
from analytics.backtest import load_matches, LEAGUES, MARKETS

GROUPS = {'osnovni': [0,1], 'teren': [0,1,2,3], 'protivnici': [0,1,4,5],
          'forma': [0,1,6], 'snaga': [0,1,7], 'odmor': [0,1,8], 'svi': list(range(9))}
FEATURES = ['napad','obrana protivnika','napad na istom terenu','obrana na istom terenu',
            'snaga ranijih protivnika napada','snaga ranijih protivnika obrane','novija forma',
            'Elo razlika','razmak ligaških utakmica']
DEV = ['2022-23', '2023-24']
AUDIT = ['2024-25', '2025-26']
BASE = dict(window=50, half_life=30, ridge=.01, group='osnovni', rho=0., temperature=1.)

def features(rows, window, half_life):
    """Sequential result release; date precision requires a >2-day embargo."""
    result = []
    leagues = defaultdict(list)
    for r in sorted(rows,key=lambda r:(r['date'],r['id'])): leagues[r['league']].append(r)
    for rs in leagues.values():
        history=[]; teams=defaultdict(list); rating=defaultdict(lambda:1500.); cursor=0
        for m in rs:
            day=date.fromisoformat(m['date']); cutoff=(day-timedelta(days=2)).isoformat()
            while cursor<len(rs) and rs[cursor]['date']<cutoff:
                r=rs[cursor]
                # Unplayed prospective fixtures get features but never enter history.
                if r.get('pending'):cursor+=1;continue
                h,a=r['home'],r['away'];rh,ra=rating[h],rating[a]
                expected=1/(1+10**((ra-rh-60)/400));out=1 if r['hg']>r['ag'] else .5 if r['hg']==r['ag'] else 0
                rating[h]+=20*(out-expected);rating[a]-=20*(out-expected)
                teams[h].append((r['hg'],r['ag'],1,ra,r['date']))
                teams[a].append((r['ag'],r['hg'],0,rh,r['date']))
                history.append(r);cursor+=1
            recent=[r for r in history[-760:] if (day-date.fromisoformat(r['date'])).days<=730]
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
                gf,ga=rates(vals,weights)
                same=[(v,w) for v,w in zip(vals,weights) if v[2]==venue]
                vgf,vga=rates([v for v,w in same],[w for v,w in same])
                strength=sum(w*(v[3]-1500)/400 for v,w in zip(vals,weights))/(sum(weights)+8)
                last=vals[-5:];form=sum(3 if v[0]>v[1] else 1 if v[0]==v[1] else 0 for v in last)/len(last)
                rest=min(14,max(2,(day-date.fromisoformat(vals[-1][4])).days))
                return gf,ga,vgf,vga,strength,form,rest
            h,a=stats(m['home'],1),stats(m['away'],0)
            if h is None or a is None:continue
            def vector(own,opp,rt):
                return [np.log(own[0]/mean),np.log(opp[1]/mean),np.log(own[2]/own[0]),np.log(opp[3]/opp[1]),own[4],opp[4],(own[5]-opp[5])/3,rt/400,(own[6]-opp[6])/12]
            x=[vector(h,a,rating[m['home']]-rating[m['away']]),vector(a,h,rating[m['away']]-rating[m['home']])]
            result.append(dict(match=m,x=x,offset=[np.log(max(.1,hb)),np.log(max(.1,ab))],history_end=history[-1]['date']))
    return sorted(result,key=lambda r:(r['match']['date'],r['match']['id']))

def arrays(records, cols):
    x=np.array([r['x'] for r in records],dtype=float).reshape(-1,9)[:,cols]
    offset=np.array([r['offset'] for r in records]).reshape(-1)
    y=np.array([[r['match']['hg'],r['match']['ag']] for r in records]).reshape(-1)
    return x,offset,y

def fit(records, config):
    cols=GROUPS[config['group']];x,offset,y=arrays(records,cols)
    center=x.mean(axis=0);scale=x.std(axis=0);scale=np.where(scale<1e-6,1.,scale)
    z=np.column_stack([np.ones(len(x)),(x-center)/scale]);penalty=np.ones(z.shape[1]);penalty[0]=0
    def objective(beta):
        eta=offset+z@beta;lam=np.exp(eta)
        return np.mean(lam-y*eta)+.5*config['ridge']*np.sum(penalty*beta**2), z.T@(lam-y)/len(y)+config['ridge']*penalty*beta
    opt=minimize(objective,np.zeros(z.shape[1]),jac=True,method='L-BFGS-B',bounds=[(-3,3)]*z.shape[1],options={'maxiter':120,'ftol':1e-10})
    if not opt.success:raise RuntimeError('Poisson optimizer failed: '+str(opt.message))
    return dict(beta=opt.x,center=center,scale=scale,cols=cols,training_matches=len(records))

def intensities(records, model):
    x,offset,_=arrays(records,model['cols']);z=np.column_stack([np.ones(len(x)),(x-model['center'])/model['scale']])
    return np.exp(np.clip(offset+z@model['beta'],np.log(.15),np.log(6))).reshape(-1,2)

def probability_array(lam, rho=0., temperature=1.):
    h,a=lam[:,0],lam[:,1]
    # Bound the low-score correction so all four underlying score cells stay nonnegative.
    effective_rho=np.clip(rho,np.maximum(-1/h,-1/a)+1e-9,np.minimum(1.,1/(h*a))-1e-9)
    delta=effective_rho*h*a*np.exp(-h-a)
    p=np.column_stack([skellam.sf(0,h,a)+delta,skellam.pmf(0,h,a)-2*delta,skellam.cdf(-1,h,a)+delta])
    p=np.clip(p,1e-9,1.);p=p**(1/temperature);p/=p.sum(axis=1,keepdims=True)
    total=h+a;over=1-np.exp(-total)*(1+total+total**2/2);over=np.clip(over,1e-9,1-1e-9)
    over=1/(1+np.exp(-np.log(over/(1-over))/temperature))
    return np.column_stack([p,over,1-over])

def actual_array(records):
    h=np.array([r['match']['hg'] for r in records]);a=np.array([r['match']['ag'] for r in records])
    return np.column_stack([h>a,h==a,h<a,h+a>2.5,h+a<2.5]).astype(float)

def metrics(p, y):
    if len(p)==0:return None
    b=(p-y)**2;score=(b[:,:3].mean(axis=1)+b[:,3])/2
    ix=np.arange(len(p));pick=p.argmax(axis=1)
    def bins(column):
        out=[]
        for k in range(10):
            use=np.minimum(9,(p[:,column]*10).astype(int))==k
            if use.any():out.append(dict(n=int(use.sum()),prob=float(p[use,column].mean()),rate=float(y[use,column].mean())))
        return out
    return dict(matches=len(p),family_brier=float(score.mean()),outcome_log_loss=float(-np.log(np.clip(p[:,:3][y[:,:3].astype(bool)],1e-9,1)).mean()),goals_log_loss=float(-(y[:,3]*np.log(np.clip(p[:,3],1e-9,1))+(1-y[:,3])*np.log(np.clip(1-p[:,3],1e-9,1))).mean()),outcome_hit_rate=float(y[ix,p[:,:3].argmax(axis=1)].mean()),goals_hit_rate=float(y[ix,3+(p[:,3]<.5)].mean()),top_pick_hit_rate=float(y[ix,pick].mean()),top_pick_mean_probability=float(p[ix,pick].mean()),calibration={m:bins(i) for i,m in enumerate(MARKETS)})

def records_before(records, season):
    # Calendar split with embargo even at the boundary; no later-season training.
    start=min(r['match']['date'] for r in records if r['match']['season']==season)
    cutoff=(date.fromisoformat(start)-timedelta(days=2)).isoformat()
    return [r for r in records if r['match']['season']<season and r['match']['date']<cutoff]

def evaluate_dev(records, config):
    parts=[];ys=[];folds=[]
    for season in DEV:
        train=records_before(records,season);val=[r for r in records if r['match']['season']==season]
        model=fit(train,config);parts.append(intensities(val,model));ys.append(actual_array(val));folds.append((season,len(val)))
    return np.concatenate(parts),np.concatenate(ys),folds

def stripped(m):return {k:v for k,v in m.items() if k!='calibration'}

def run(data,output,ui):
    rows,source=load_matches(data);out=Path(output)
    if (out/'expanded-report.json').exists():raise FileExistsError('Completed run exists; choose a new --output directory to preserve the audit trail')
    out.mkdir(parents=True,exist_ok=True)
    trial_path=out/'expanded-trials.jsonl';trials=[];cache={};trial_id=0
    with trial_path.open('w') as stream:
        for window,half in itertools.product((10,20,50),(5,15,30)):
            rec=features(rows,window,half);cache[(window,half)]=rec
            for ridge,group in itertools.product((.001,.01,.1),GROUPS):
                config=dict(window=window,half_life=half,ridge=ridge,group=group)
                lam,y,folds=evaluate_dev(rec,config)
                for rho,temp in itertools.product((-.1,0.,.1),(.85,1.,1.15)):
                    full={**config,'rho':rho,'temperature':temp};p=probability_array(lam,rho,temp)
                    # Equal season weights, so a larger league-season cannot dominate selection by year.
                    pos=0;fold_metrics={}
                    for season,n in folds:fold_metrics[season]=stripped(metrics(p[pos:pos+n],y[pos:pos+n]));pos+=n
                    trial=dict(id=trial_id,config=full,score=float(np.mean([v['family_brier'] for v in fold_metrics.values()])),folds=fold_metrics)
                    trials.append(trial);stream.write(json.dumps(trial,ensure_ascii=False)+'\n');trial_id+=1
            print(json.dumps(dict(progress=trial_id,window=window,half_life=half)),flush=True)
    chosen=min(trials,key=lambda t:(t['score'],t['id']))
    lock=dict(protocol='expanded-v1',selected_config=chosen['config'],selection_seasons=DEV,selection_score=chosen['score'],trials=len(trials),source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),audit_status='Previously viewed seasons: descriptive reanalysis, NOT an independent final test',prospective_test='Unseen future results after model lock; no results claimed')
    (out/'expanded-lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    cfg=chosen['config'];rec=cache[(cfg['window'],cfg['half_life'])]
    audit=[r for r in rec if r['match']['season'] in AUDIT]
    train=records_before(rec,AUDIT[0]);model=fit(train,cfg)
    p=probability_array(intensities(audit,model),cfg['rho'],cfg['temperature']);y=actual_array(audit)
    lam=np.exp(np.array([r['offset'] for r in audit]));reference=probability_array(lam)
    # All alternatives evaluated on exactly the same fixtures.
    lookup={r['match']['id']:r for r in cache[(50,30)]};base_records=[lookup[r['match']['id']] for r in audit]
    best_base=min((t for t in trials if t['config']['group']=='osnovni'),key=lambda t:(t['score'],t['id']))
    bc=best_base['config'];base_context=cache[(bc['window'],bc['half_life'])]
    base_lookup={r['match']['id']:r for r in base_context};base_records=[base_lookup[r['match']['id']] for r in audit]
    base_model=fit(records_before(base_context,AUDIT[0]),bc)
    base=probability_array(intensities(base_records,base_model),bc['rho'],bc['temperature'])
    ablations=[]
    for group in GROUPS:
        best=min((t for t in trials if t['config']['group']==group),key=lambda t:(t['score'],t['id']))
        family=dict(group=group,development_score=best['score'],delta_vs_base=best_base['score']-best['score'],config=best['config'])
        for field in ('outcome_log_loss','goals_log_loss'):
            family[field]=float(np.mean([v[field] for v in best['folds'].values()]))
            family[field+'_improvement']=float(np.mean([v[field] for v in best_base['folds'].values()]))-family[field]
        ablations.append(family)
    # Within-selected-model drop-one-block refits, all evaluated on DEVELOPMENT only.
    importance=[];all_cfg={**cfg,'group':'svi'};lam_all,dy,folds=evaluate_dev(rec,all_cfg)
    def devscore(lam):
        pp=probability_array(lam,cfg['rho'],cfg['temperature']);pos=0;s=[]
        for _,n in folds:s.append(metrics(pp[pos:pos+n],dy[pos:pos+n])['family_brier']);pos+=n
        return float(np.mean(s))
    full_score=devscore(lam_all)
    for name,drop in [('teren',[2,3]),('protivnici',[4,5]),('forma',[6]),('snaga',[7]),('odmor',[8])]:
        key='bez_'+name;GROUPS[key]=[i for i in range(9) if i not in drop]
        ll,_,_=evaluate_dev(rec,{**cfg,'group':key});score=devscore(ll)
        importance.append(dict(factor=name,score_without=score,score_full=full_score,delta=score-full_score))
    # Descriptive paired uncertainty: resample calendar weeks, not individual bets.
    def losses(pp):return (((pp-y)**2)[:,:3].mean(axis=1)+((pp-y)**2)[:,3])/2
    delta=losses(p)-losses(base);weeks=defaultdict(list)
    for r,d in zip(audit,delta):weeks[date.fromisoformat(r['match']['date']).strftime('%G-%V')].append(float(d))
    blocks=list(weeks.values());rng=np.random.default_rng(20261028);bootstrap=[]
    for _ in range(1000):
        selected=rng.integers(0,len(blocks),len(blocks));bootstrap.append(sum(sum(blocks[i]) for i in selected)/sum(len(blocks[i]) for i in selected))
    per_league={code:dict(name=name,**(stripped(metrics(p[[r['match']['league']==code for r in audit]],y[[r['match']['league']==code for r in audit]])) or {})) for code,name in LEAGUES.items()}
    report=dict(schema_version=1,generated_at=datetime.now(timezone.utc).isoformat(),status='development_reanalysis_only',dataset_matches=len(rows),leagues=LEAGUES,coverage=source['coverage'],development_seasons=DEV,audit_seasons=AUDIT,configurations_tested=len(trials),selected=chosen,lock=lock,development_leaderboard=sorted(trials,key=lambda t:(t['score'],t['id']))[:10],factor_families=ablations,drop_factor_importance=sorted(importance,key=lambda t:-t['delta']),features=FEATURES,model_weights={name:float(model['beta'][i+1]/model['scale'][i]) for i,name in enumerate([FEATURES[c] for c in model['cols']])},audit=stripped(metrics(p,y)),audit_calibration=metrics(p,y)['calibration'],baseline=stripped(metrics(base,y)),baseline_config=bc,league_reference=stripped(metrics(reference,y)),by_league=per_league,by_season={s:stripped(metrics(p[[r['match']['season']==s for r in audit]],y[[r['match']['season']==s for r in audit]])) for s in AUDIT},paired_brier_delta=dict(estimate=float(delta.mean()),weekly_bootstrap_95=[float(v) for v in np.quantile(bootstrap,[.025,.975])],interpretation='Descriptive interval; excludes model selection uncertainty; not proof of independent improvement'),limitations=['2024/25 and 2025/26 already inspected: descriptive reanalysis only; prospective holdout remains required.','Partial source coverage, especially 2025/26; no claim of complete seasons or final rounds.','No lineup, injury, tactical, xG, weather, coach, media or timestamped odds data.','Rest is time between recorded league fixtures, not actual recovery including cups/Europe.','Elo and opponent adjustment are result-derived strength proxies, not a measure of tactical style.','Team names are source strings; historical renames/transfers are not resolved globally.','Results assumed available after >2 calendar days; no archived publication timestamps.','Fixed deterministic grid, equal season Brier weighting; 1701 trials are correlated, not independent evidence.','No ROI, odds 2+ evaluation, exact-score claim or live recommendations.'])
    (out/'expanded-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/'expanded-predictions.jsonl').open('w') as f:
        for r,pp,yy in zip(audit,p,y):
            f.write(json.dumps(dict(id=r['match']['id'],date=r['match']['date'],league=r['match']['league'],season=r['match']['season'],history_end=r['history_end'],prob=dict(zip(MARKETS,pp.tolist())),actual=dict(zip(MARKETS,yy.astype(int).tolist())),status='historical_reanalysis'),ensure_ascii=False)+'\n')
    compact={k:v for k,v in report.items() if k not in ('audit_calibration','development_leaderboard','coverage','model_weights','features','lock')}
    Path(ui).write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(trials=len(trials),selected=cfg,audit=report['audit'],baseline=report['baseline']),ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--output',default='data/experiments/expanded-v1');p.add_argument('--ui',default='app/expanded-summary.json');a=p.parse_args();run(a.data,a.output,a.ui)
