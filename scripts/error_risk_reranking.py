"""Leakage-safe risk-aware reranking experiment.

Only previous seasons are used to fit a model estimating whether the base pick
will be wrong. This is research; no live deployment or guaranteed correctness.
"""
import argparse,json
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scripts.second_stage_walkforward import candidate
from scripts.top25_single_pick import MARKETS,select

def evaluate(rows,min_training=500):
    seasons=sorted({str(r['season']) for r in rows})
    reports=[]
    for season in seasons:
        training=[r for r in rows if str(r['season'])<season]
        test=[r for r in rows if str(r['season'])==season]
        samples=[(candidate(r),r) for r in training]
        samples=[(c,r) for c,r in samples if c and 'actual' in r and c[0] in r['actual']]
        if len(samples)<min_training:continue
        x=[c[1] for c,r in samples]
        y=[int(not bool(r['actual'][c[0]])) for c,r in samples]
        if len(set(y))<2:continue
        models={
            'logistic':make_pipeline(StandardScaler(),LogisticRegression(max_iter=500)),
            'nonlinear':HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,
                min_samples_leaf=80,l2_regularization=10,early_stopping=False,random_state=0)
        }
        base=select(test)
        results={}
        for name,model in models.items():
            model.fit(x,y)
            altered=[]
            original={}
            for r in test:
                c=candidate(r)
                if c is None:
                    altered.append(r)
                    continue
                risk=float(model.predict_proba([c[1]])[0][1])
                # Select by estimated probability of a CORRECT base-market pick.
                # Never let the risk score change which market was originally picked.
                score=max(1e-9,1-risk)
                altered.append(dict(r,prob={m:(score if m==c[0] else 0.) for m in MARKETS}))
                original[r['id']]=c[0]
            proposed=select(altered)
            for pick in proposed['selected']:
                pick['market']=original[pick['id']]
            results[name]={
                'summary':proposed['summary'],
                'selected_ids':[r['id'] for r in proposed['selected']],
                'changed_from_baseline':len(set(r['id'] for r in proposed['selected']) ^
                                            set(r['id'] for r in base['selected']))//2}
        reports.append({'season':season,'training':len(samples),
                        'baseline':base['summary'],'challengers':results})
    return {'research_only':True,'method':'earlier-season error-risk reranking',
            'seasons':reports,'warning':'Retrospective archive is already viewed; no future accuracy proven.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    rows=[json.loads(s) for s in Path(a.input).read_text().splitlines() if s.strip()]
    result=evaluate(rows)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    for s in result['seasons']:
        print(json.dumps({'season':s['season'],'baseline':s['baseline'],
                          'challengers':{k:v['summary'] for k,v in s['challengers'].items()}}),flush=True)
if __name__=='__main__':main()
