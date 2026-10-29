"""Residual calibration and abstention gates, chosen without audit outcomes.

Inherited seeds used viewed development seasons; the entire experiment remains
exploratory. Unknown results participate in selection. No live recommendations.
"""
import argparse
import hashlib
import itertools
import json
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from scipy.stats import norm
from analytics.backtest import LEAGUES, MARKETS
from analytics.expanded_search import features, actual_array, metrics, stripped
from analytics.market_specialists import chronological_predictions, combine
from analytics.filter_audit import all_fixtures, offers, analyze, summary

CONFIGS = [dict(id='identity', local=False, ridge=None)]+[
    dict(id=f'{scope}-{ridge}', local=scope=='league', ridge=ridge)
    for scope, ridge in itertools.product(('pooled', 'league'), (.01, .1, 1.))]
RULES = [dict(id=f'{profile}-p{int(p*100)}', profile=profile, threshold=p)
         for profile,p in itertools.product(('all', 'agree', 'history', 'history_agree'),
                                            (0., .6, .7, .8, .85, .9, .95))]


def design(leagues, supported):
    return np.column_stack([np.ones(len(leagues))]+[
        np.array([float(v==code) for v in leagues]) for code in supported])


def fit_calibration(p, y, leagues, config):
    if config['id']=='identity':
        return dict(config=config, supported=[], scale=1., bias=[])
    supported = [code for code in LEAGUES if leagues.count(code)>=200] if config['local'] else []
    x=design(leagues, supported); lp=np.log(np.clip(p, 1e-9, 1)); n,k=p.shape
    target=np.eye(k)[y]; ridge=config['ridge']
    def objective(theta):
        scale=theta[0]; bias=theta[1:].reshape(x.shape[1], k)
        eta=lp*scale+x@bias; pp=softmax(eta, axis=1)
        err=(pp-target)/n
        value=-np.log(np.clip(pp[np.arange(n),y],1e-12,1)).mean()
        value+=.5*ridge*((scale-1)**2+np.sum(bias*bias))
        grad=np.r_[np.sum(err*lp)+ridge*(scale-1), (x.T@err+ridge*bias).ravel()]
        return value,grad
    initial=np.zeros(1+x.shape[1]*k); initial[0]=1
    opt=minimize(objective, initial, jac=True, method='L-BFGS-B',
                 bounds=[(.25,4.)]+[(-2.,2.)]*(len(initial)-1), options={'maxiter':300,'ftol':1e-12})
    if not opt.success:
        raise RuntimeError('Calibration did not converge: '+str(opt.message))
    return dict(config=config, supported=supported, scale=float(opt.x[0]),
                bias=opt.x[1:].reshape(x.shape[1],k).tolist())


def apply_calibration(p, leagues, model):
    if model['config']['id']=='identity':
        return p.copy()
    return softmax(np.log(np.clip(p,1e-9,1))*model['scale']+
                   design(leagues,model['supported'])@np.array(model['bias']),axis=1)


def select_calibrator(trials):
    return min(trials,key=lambda r:(r['development_log_loss'],r['config']['id']))


def history_quality(rows):
    """Pre-match counts and days since recorded league result; NOT full rest."""
    history=defaultdict(list); quality={}; cursor=0
    for target in rows:
        cutoff=(date.fromisoformat(target['date'])-timedelta(days=2)).isoformat()
        while cursor<len(rows) and rows[cursor]['date']<cutoff:
            old=rows[cursor]; cursor+=1
            if old.get('pending'):
                continue
            for side in ('home','away'):
                history[(old['league'],old[side])].append(old['date'])
        hs=[history[(target['league'],target[side])] for side in ('home','away')]
        quality[target['id']]=dict(min_history=min(map(len,hs)),
            max_recorded_gap=max((date.fromisoformat(target['date'])-date.fromisoformat(h[-1])).days if h else 9999 for h in hs))
    return quality


def pick_pool(records, corrected, raw, quality):
    """One highest-probability offer per fixture, before revealing outcomes."""
    out=[]
    for r,p,base in zip(records,corrected,raw):
        m=r['match']; col=int(np.argmax(p)); actual=actual_array([r])[0,col]
        out.append(dict(id=m['id']+'|'+MARKETS[col],match_id=m['id'],league=m['league'],
            season=m['season'],date=m['date'],market=MARKETS[col],prob=float(p[col]),
            actual=None if m.get('pending') else int(actual),
            agrees=col==int(np.argmax(base)),**quality[m['id']]))
    return out


def select_gate(pool, rule):
    rich=rule['profile'] in ('history','history_agree')
    agree=rule['profile'] in ('agree','history_agree')
    return [r for r in pool if r['prob']>=rule['threshold']
            and (not rich or (r['min_history']>=20 and r['max_recorded_gap']<=21))
            and (not agree or r['agrees'])]


def lower_bound(hits,n,comparisons):
    if not n:
        return None
    # Bonferroni-adjusted one-sided Wilson: descriptive screening only.
    z=norm.ppf(1-.05/comparisons); p=hits/n; den=1+z*z/n
    return float((p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/den)


def gate_report(pool,rule):
    selected=select_gate(pool,rule); s=summary(selected,pool)
    s.update(rule=rule,simultaneous_lower95=lower_bound(s['hits'],s['scored'],len(RULES)),
             scored_unique_matches=len({r['match_id'] for r in selected if r['actual'] is not None}))
    s['development_90_screen']=bool(s['scored_unique_matches']>=200 and s['simultaneous_lower95']>.9)
    return s


def choose_gate(reports):
    eligible=[r for r in reports if r['development_90_screen']]
    return max(eligible,key=lambda r:(r['scored_unique_matches'],r['rule']['id']))['rule'] if eligible else None


def run(data,source_lock,output,ui):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows,source=all_fixtures(data); source_model=json.loads(Path(source_lock).read_text())
    quality=history_quality(rows); caches={}; prediction_cache={}; traces={}
    def predict(season):
        if season in prediction_cache:
            return prediction_cache[season]
        families={}; common=None; targets=None
        for family,cfg in source_model['seed_configs'].items():
            key=(cfg['window'],cfg['half_life'])
            if key not in caches:
                caches[key]=features(rows,*key)
            p,rec,trace=chronological_predictions(caches[key],season,cfg,source_model['chosen'][family]['policy'])
            ids=[r['match']['id'] for r in rec]
            if common is not None and ids!=common:
                raise ValueError('Mismatched calibration fixtures')
            common=ids; targets=rec; families[family]=p; traces[f'{season}:{family}']=trace
        prediction_cache[season]=(targets,combine(families['outcome'],families['goals']))
        return prediction_cache[season]
    def scored(records,p):
        mask=np.array([not r['match'].get('pending') for r in records])
        return [r for r in records if not r['match'].get('pending')],p[mask]
    train,pt=scored(*predict('2022-23')); dev,pd=predict('2023-24')
    dev_scored,pds=scored(dev,pd); models={}; trials={}; selected={}
    for family,cols in (('outcome',slice(0,3)),('goals',slice(3,5))):
        yt=actual_array(train)[:,cols].argmax(axis=1); yd=actual_array(dev_scored)[:,cols].argmax(axis=1)
        trials[family]=[]; models[family]={}
        for cfg in CONFIGS:
            model=fit_calibration(pt[:,cols],yt,[r['match']['league'] for r in train],cfg)
            pred=apply_calibration(pds[:,cols],[r['match']['league'] for r in dev_scored],model)
            trial=dict(config=cfg,development_log_loss=float(-np.log(np.clip(pred[np.arange(len(yd)),yd],1e-12,1)).mean()))
            trials[family].append(trial);models[family][cfg['id']]=model
        selected[family]=select_calibrator(trials[family])['config']['id']
    def correct(records,p):
        leagues=[r['match']['league'] for r in records]
        return np.column_stack([apply_calibration(p[:,:3],leagues,models['outcome'][selected['outcome']]),
                                apply_calibration(p[:,3:],leagues,models['goals'][selected['goals']])])
    dev_corrected=correct(dev,pd); dev_pool=pick_pool(dev,dev_corrected,pd,quality)
    dev_gates=[gate_report(dev_pool,rule) for rule in RULES]; gate=choose_gate(dev_gates)
    lock=dict(name='confidence-search-v1',created_at=datetime.now(timezone.utc).isoformat(),
              calibration_fit='2022-23',calibration_selection_and_gate='2023-24',audit=['2024-25','2025-26'],
              inherited_development_warning='Base seeds/policies previously selected on both development seasons; not a fresh independent development split.',
              selected=selected,models={f:models[f][selected[f]] for f in models},rules=RULES,selected_gate=gate,
              gate_selection='>=200 distinct scored fixtures and Bonferroni one-sided Wilson lower95 >.90; max coverage; else no gate.',
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              source_lock_sha256=hashlib.sha256(Path(source_lock).read_bytes()).hexdigest(),
              source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
              audit_status='Previously viewed audit: descriptive reanalysis only. No independent 90% proof.')
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    rec=[];ps=[]
    for season in ('2024-25','2025-26'):
        rr,pp=predict(season);rec.extend(rr);ps.append(pp)
    raw=np.concatenate(ps); adjusted=correct(rec,raw); pool=pick_pool(rec,adjusted,raw,quality)
    scored_rec,scored_raw=scored(rec,raw);_,scored_adjusted=scored(rec,adjusted); truth=actual_array(scored_rec)
    report=dict(protocol=lock,calibration_candidates=trials,development_gates=dev_gates,
                audit_gates=[gate_report(pool,rule) for rule in RULES],
                eligible_fixtures=len(rec),unscored_fixtures=sum(r['match'].get('pending',False) for r in rec),
                reference=stripped(metrics(scored_raw,truth)),candidate=stripped(metrics(scored_adjusted,truth)),
                selected_gate_audit=gate_report(pool,gate) if gate else None,
                independent_90_confirmed=False,promoted=False,
                daily_reference=analyze(offers(rec,raw)),daily_candidate=analyze(offers(rec,adjusted)),
                by_league={code:dict(name=name,reference=stripped(metrics(scored_raw[np.array([r['match']['league']==code for r in scored_rec])],truth[np.array([r['match']['league']==code for r in scored_rec])])),
                                                     candidate=stripped(metrics(scored_adjusted[np.array([r['match']['league']==code for r in scored_rec])],truth[np.array([r['match']['league']==code for r in scored_rec])]))) for code,name in LEAGUES.items()},
                training_trace=traces,
                limitations=['No new external facts; correction of existing result-derived model probabilities.',
                             'One offer per fixture in new gate analysis; existing daily Top10/50 still allow multiple offers.',
                             'Unknown outcomes retained in all selection pools; no hidden losses.',
                             'Recorded league-result gap is not complete rest; missing cups/Europe and source gaps.',
                             'Multiplicity bound is an exploratory screen, not independence or prospective proof.',
                             'Previously viewed seasons, inherited development tuning and no archived result-publication timestamps.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'predictions.jsonl').open('x') as stream:
        for r,p,b in zip(rec,adjusted,raw):
            stream.write(json.dumps(dict(id=r['match']['id'],date=r['match']['date'],pending=r['match'].get('pending',False),prob=p.tolist(),reference=b.tolist()))+'\n')
    with (out/'gate-pool.jsonl').open('x') as stream:
        for row in pool:stream.write(json.dumps(row)+'\n')
    if ui:
        Path(ui).write_text(json.dumps({k:v for k,v in report.items() if k not in ('training_trace','by_league')},indent=2)+'\n')
    print(json.dumps(dict(selected=selected,selected_gate=gate,reference=report['reference'],candidate=report['candidate'],audit_gates=[{k:v for k,v in r.items() if k in ('rule','hits','misses','scored','unscored','hit_rate','match_coverage')} for r in report['audit_gates']]),indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/openfootball');p.add_argument('--source-lock',default='data/experiments/20261029-market-specialists-v1/specialists-lock.json');p.add_argument('--output',required=True);p.add_argument('--ui',default='app/confidence-summary.json');a=p.parse_args();run(a.data,a.source_lock,a.output,a.ui)
