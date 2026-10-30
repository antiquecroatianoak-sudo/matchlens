"""Create paired, frozen, prematch-only shadow predictions from existing fixture probabilities.

Input rows must have no actual outcome and must represent future fixtures.
The historical training file is used ONLY to fit the challenger.
"""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scripts.second_stage_walkforward import candidate
from scripts.top25_single_pick import MARKETS,select

def shadow(history,fixtures,min_training=500):
    if not fixtures:raise ValueError('No upcoming fixtures supplied')
    if any('actual' in r for r in fixtures):
        raise ValueError('Upcoming fixture rows must not contain outcomes')
    ids=[r['id'] for r in fixtures]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate upcoming fixture IDs')
    train=[(candidate(r),r) for r in history]
    train=[(c,r) for c,r in train if c and 'actual' in r and c[0] in r['actual']]
    if len(train)<min_training:raise ValueError('Insufficient historical training examples')
    x=[c[1] for c,r in train];y=[int(bool(r['actual'][c[0]])) for c,r in train]
    if len(set(y))<2:raise ValueError('Historical labels have only one class')
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500))
    model.fit(x,y)
    reranked=[]
    for r in fixtures:
        c=candidate(r)
        if c is None:
            reranked.append(r)
            continue
        reliability=float(model.predict_proba([c[1]])[0][1])
        reranked.append(dict(r,prob={m:(reliability if m==c[0] else 0.0) for m in MARKETS}))
    old=select(fixtures);new=select(reranked)
    market_by_id={r['id']:candidate(r)[0] for r in fixtures if candidate(r)}
    for pick in new['selected']:
        pick['market']=market_by_id[pick['id']]
        pick['model_reliability_score']=pick.pop('probability')
        pick['original_market_probability']=next(r['prob'][pick['market']] for r in fixtures if r['id']==pick['id'])
    return {'generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'mode':'shadow_only_not_live','historical_training_rows':len(train),
            'baseline':old,'challenger':new,
            'warning':'Predictions must be frozen before kickoff and evaluated only after results arrive.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--history',required=True)
    p.add_argument('--upcoming',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    read=lambda path:[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    report=shadow(read(args.history),read(args.upcoming))
    out=Path(args.output)
    if out.exists():raise FileExistsError('Refusing to overwrite frozen predictions')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('SHADOW PREDICTIONS FROZEN',report['generated_at_utc'],
          report['baseline']['summary']['selected'],report['challenger']['summary']['selected'])
if __name__=='__main__':main()
