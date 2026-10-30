"""Retrospective expanding-window evaluation; model choices previously inspected, NOT unseen validation."""
import argparse,json
from datetime import date, timedelta
from pathlib import Path
import numpy as np
from analytics.backtest import load_matches,MARKETS
from analytics.expanded_search import features,actual_array
from analytics.factor_search import build_design,training_mask,learner,GROUPS,probabilities

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',default='data/openfootball')
    parser.add_argument('--lock',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--start-date',default='2024-10-30')
    parser.add_argument('--end-date',default='2026-10-30')
    args=parser.parse_args()
    lock=json.loads(Path(args.lock).read_text())
    rows,_=load_matches(args.data)
    rows=[r for r in rows if args.start_date <= r['date'] <= args.end_date]
    records=features(rows,50,15)
    x=build_design(rows,records)
    y=actual_array(records)
    seasons=np.array([r['match']['season'] for r in records])
    labels={'outcome':y[:,:3].argmax(axis=1),'goals':y[:,3].astype(int)}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    with output.open('w') as stream:
        for season in sorted(set(seasons)):
            if not any(args.start_date <= r['match']['date'] <= args.end_date for r in records if r['match']['season']==season):continue
            test=seasons==season
            train=training_mask(records,season)
            if train.sum()<100 or test.sum()<30:continue
            raw={}
            for family in ('outcome','goals'):
                config=lock['chosen'][family]['config']
                cols=GROUPS[config['group']]
                model=learner(config).fit(x[train][:,cols],labels[family][train])
                pred=model.predict_proba(x[test][:,cols])
                raw[family]=pred if family=='outcome' else pred[:,1]
            p=probabilities(raw['outcome'],raw['goals'],lock['temperatures']['outcome'],lock['temperatures']['goals'])
            subset=[r for r,flag in zip(records,test) if flag]
            for r,prob,actual in zip(subset,p,y[test]):
                stream.write(json.dumps({'id':r['match']['id'],'date':r['match']['date'],
                    'prob':dict(zip(MARKETS,prob.tolist())),
                    'actual':dict(zip(MARKETS,actual.tolist()))})+'\n')
            results.append({'season':season,'training':int(train.sum()),'evaluated':len(subset)})
            print(json.dumps(results[-1]),flush=True)
    print('RETROSPECTIVE ONLY: model configuration and temperatures were chosen using already-viewed seasons.',flush=True)
    print('Walk-forward total:',sum(r['evaluated'] for r in results),flush=True)

if __name__=='__main__':main()
