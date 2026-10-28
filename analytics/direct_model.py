"""A new development cycle: direct 1X2 / goals classification and result-history features.
Tune 2022/23, temperature calibration 2023/24, descriptive reanalysis 2024-26.
Does not modify the expanded-v1 lock or its prospective predictions.
"""
import argparse,json,hashlib
from pathlib import Path
from collections import defaultdict
from datetime import date,timedelta,datetime,timezone
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logsumexp,softmax
from analytics.backtest import load_matches,LEAGUES,MARKETS
from analytics.expanded_search import features,records_before,actual_array,metrics,stripped

GROUPS={'strength':list(range(6)),'context':list(range(20)),'history':list(range(38))}

def history_extras(rows,records):
    by_league=defaultdict(list);targets=defaultdict(list);out={}
    for r in rows:by_league[r['league']].append(r)
    for r in records:targets[r['match']['league']].append(r)
    for league,rs in by_league.items():
        rs=sorted(rs,key=lambda r:(r['date'],r['id']));teams=defaultdict(list);h2h=defaultdict(list);cursor=0
        for rec in targets[league]:
            m=rec['match'];cutoff=(date.fromisoformat(m['date'])-timedelta(days=2)).isoformat()
            while cursor<len(rs) and rs[cursor]['date']<cutoff:
                r=rs[cursor];cursor+=1
                if r.get('pending'):continue
                h,a=r['home'],r['away'];teams[h].append((r['hg'],r['ag']));teams[a].append((r['ag'],r['hg']))
                h2h[tuple(sorted((h,a)))].append(r)
            def stats(team):
                vals=teams[team][-10:];gf=np.array([v[0] for v in vals]);ga=np.array([v[1] for v in vals])
                return [(gf+ga).mean(),(gf+ga).std(),(ga==0).mean(),(gf==0).mean(),(gf==ga).mean(),gf[-3:].mean()-gf.mean()]
            hh=h2h[tuple(sorted((m['home'],m['away'])))][-3:]
            diff=sum((r['hg']-r['ag'])*(1 if r['home']==m['home'] else -1) for r in hh)/(len(hh)+5)
            total=(sum(r['hg']+r['ag'] for r in hh)+5*2.5)/(len(hh)+5)
            x=np.array(rec['x']);elo=x[0,7]
            out[m['id']]=stats(m['home'])+stats(m['away'])+[diff,total,elo*abs(elo),abs(elo),x[0,0]*x[0,1],x[1,0]*x[1,1]]
    return out

def design(records,extra):
    result=[]
    for r in records:
        x=np.array(r['x']).flatten();off=r['offset']
        # First six are the two teams' scoring/conceding rates and Elo difference.
        order=[0,1,7,9,10,16]+[i for i in range(18) if i not in (0,1,7,9,10,16)]
        result.append(x[order].tolist()+off+extra[r['match']['id']])
    return np.array(result)

def fit_direct(x,y,cols,ridge):
    xx=x[:,cols];center=xx.mean(axis=0);scale=xx.std(axis=0);scale=np.where(scale<1e-6,1,scale)
    z=np.column_stack([np.ones(len(xx)),(xx-center)/scale]);pen=np.ones(z.shape[1]);pen[0]=0
    def objective(beta):
        coef=beta.reshape(4,-1);logit=z@coef[:3].T;goal=z@coef[3];p=softmax(logit,axis=1);g=expit(goal)
        loss=np.mean(logsumexp(logit,axis=1)-np.sum(logit*y[:,:3],axis=1))+np.mean(np.logaddexp(0,goal)-y[:,3]*goal)+.5*ridge*np.sum(coef**2*pen)
        grad=np.vstack([(p-y[:,:3]).T@z/len(z),(g-y[:,3])@z/len(z)])+ridge*coef*pen
        return loss,grad.ravel()
    opt=minimize(objective,np.zeros(4*z.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':250,'ftol':1e-10})
    if not opt.success:raise RuntimeError(str(opt.message))
    return dict(beta=opt.x.reshape(4,-1),center=center,scale=scale,cols=cols)

def predict_direct(x,model,temp=1.):
    z=np.column_stack([np.ones(len(x)),(x[:,model['cols']]-model['center'])/model['scale']]);l=z@model['beta'].T
    p=softmax(l[:,:3]/temp,axis=1);over=expit(l[:,3]/temp)
    return np.column_stack([p,over,1-over])

def run(data,output,ui):
    out=Path(output)
    if (out/'direct-report.json').exists():raise FileExistsError('Use new experiment directory')
    out.mkdir(parents=True,exist_ok=True);rows,source=load_matches(data);records=features(rows,50,15)
    extra=history_extras(rows,records);x=design(records,extra);y=actual_array(records)
    seasons=np.array([r['match']['season'] for r in records]);dates=np.array([r['match']['date'] for r in records])
    def training_before(season):
        start=min(dates[seasons==season]);cutoff=(date.fromisoformat(start)-timedelta(days=2)).isoformat()
        return (seasons<season)&(dates<cutoff)
    tuning=seasons=='2022-23';trials=[]
    for name,cols in GROUPS.items():
        for ridge in (.001,.01,.1,1.):
            train=training_before('2022-23');m=fit_direct(x[train],y[train],cols,ridge);p=predict_direct(x[tuning],m)
            trials.append(dict(group=name,ridge=ridge,tuning=stripped(metrics(p,y[tuning]))))
    chosen=min(trials,key=lambda r:r['tuning']['family_brier']);cols=GROUPS[chosen['group']]
    cal=seasons=='2023-24';train=training_before('2023-24');cm=fit_direct(x[train],y[train],cols,chosen['ridge']);cal_trials=[]
    for temp in (.75,.85,1.,1.15,1.3,1.5):cal_trials.append(dict(temperature=temp,metrics=stripped(metrics(predict_direct(x[cal],cm,temp),y[cal]))))
    selected_temp=min(cal_trials,key=lambda r:r['metrics']['family_brier'])['temperature']
    lock=dict(protocol='direct-v1',created_at=datetime.now(timezone.utc).isoformat(),tuning_season='2022-23',calibration_season='2023-24',config=chosen,temperature=selected_temp,candidates=len(trials),source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),extra_features=['team total-goal mean and standard deviation over last 10','clean-sheet, failed-to-score and draw frequencies','last-three scoring trend versus last ten','smoothed head-to-head goal difference and total','nonlinear Elo and attack-defense interactions'],audit_status='Already viewed seasons, descriptive comparison only')
    (out/'direct-lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    audit=np.isin(seasons,['2024-25','2025-26']);train=training_before('2024-25');model=fit_direct(x[train],y[train],cols,chosen['ridge'])
    raw=predict_direct(x[audit],model);calibrated=predict_direct(x[audit],model,selected_temp)
    # Original Poisson model frozen in development, matched to identical fixtures.
    from analytics.expanded_search import fit,intensities,probability_array
    base_cfg=dict(window=50,half_life=15,ridge=.01,group='snaga',rho=-.1,temperature=1.)
    base=fit([r for r,u in zip(records,train) if u],base_cfg);audit_rec=[r for r,u in zip(records,audit) if u]
    reference=probability_array(intensities(audit_rec,base),-.1,1.)
    report=dict(protocol=lock,trials=trials,calibration_trials=cal_trials,audit=stripped(metrics(calibrated,y[audit])),raw_audit=stripped(metrics(raw,y[audit])),reference=stripped(metrics(reference,y[audit])),by_season={s:stripped(metrics(calibrated[seasons[audit]==s],y[audit][seasons[audit]==s])) for s in ('2024-25','2025-26')},by_league={code:dict(name=name,metrics=stripped(metrics(calibrated[np.array([r['match']['league']==code for r in audit_rec])],y[audit][np.array([r['match']['league']==code for r in audit_rec])]))) for code,name in LEAGUES.items()},limitations=['No independent final test; both audit seasons already viewed.','New factors describe historical results, not pressing, formations, player availability or tactical style.','Head-to-head samples are heavily smoothed; no claim of stable matchup causality.','Calibrated/raw alternatives both reported, no post-audit model promotion.','No live predictions or odds; partial source coverage remains.'])
    (out/'direct-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');Path(ui).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/'direct-predictions.jsonl').open('w') as f:
        for r,p,a in zip(audit_rec,calibrated,y[audit]):f.write(json.dumps(dict(id=r['match']['id'],date=r['match']['date'],prob=dict(zip(MARKETS,p.tolist())),actual=dict(zip(MARKETS,a.astype(int).tolist()))))+'\n')
    print(json.dumps({k:report[k] for k in ('audit','raw_audit','reference')}),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--output',default='data/experiments/20261028-direct-v1');p.add_argument('--ui',default='app/direct-summary.json');a=p.parse_args();run(a.data,a.output,a.ui)
