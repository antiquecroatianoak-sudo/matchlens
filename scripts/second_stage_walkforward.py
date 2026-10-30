"""Research-only second-stage reliability model; strictly earlier-season training."""
import argparse,collections,json,math
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scripts.top25_single_pick import MARKETS,select

def candidate(r):
    p=r['prob']
    if not all(m in p and isinstance(p[m],(int,float)) and math.isfinite(p[m]) and 0<=p[m]<=1 for m in MARKETS):
        return None
    market=max(MARKETS,key=lambda m:(p[m],-MARKETS.index(m)))
    family=MARKETS[:3] if market in MARKETS[:3] else MARKETS[3:]
    margin=p[market]-max(p[m] for m in family if m!=market)
    features=[p[market],margin,max(p[m] for m in MARKETS[:3]),
              max(p[m] for m in MARKETS[3:])]
    features += [int(market==m) for m in MARKETS]
    return market,features

def evaluate(rows,min_training=500):
    seasons=sorted({str(r['season']) for r in rows})
    reports=[]
    for season in seasons:
        train=[r for r in rows if str(r['season'])<season]
        test=[r for r in rows if str(r['season'])==season]
        x=[];y=[]
        for r in train:
            c=candidate(r)
            if c and 'actual' in r and c[0] in r['actual']:
                x.append(c[1]);y.append(int(bool(r['actual'][c[0]])))
        if len(x)<min_training or len(set(y))<2:
            continue
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500))
        model.fit(x,y)
        scored=[]
        for r in test:
            c=candidate(r)
            if c is None:continue
            reliability=float(model.predict_proba([c[1]])[0][1])
            # Use identical selected market, change only match ranking.
            altered=dict(r,prob={m:(reliability if m==c[0] else 0.) for m in MARKETS})
            scored.append(altered)
        proposed=select(scored)
        baseline=select(test)
        # Scores in altered rows are ranking estimates, not original market probabilities.
        reports.append({'season':season,'train_rows':len(x),
                        'candidate':proposed['summary'],'baseline':baseline['summary'],
                        'selected_ids':[r['id'] for r in proposed['selected']]})
    return {'method':'earlier-seasons-only logistic reliability reranking',
            'research_only':True,'seasons':reports,
            'warning':'Previously inspected archive: retrospective validation, not independent deployment evidence.'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    rows=[json.loads(x) for x in Path(args.input).read_text().splitlines() if x.strip()]
    result=evaluate(rows)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n')
    print('SECOND STAGE WALKFORWARD',json.dumps([{k:v for k,v in s.items() if k!='selected_ids'} for s in result['seasons']]),flush=True)
if __name__=='__main__':main()
