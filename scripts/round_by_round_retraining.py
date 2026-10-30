"""Chronological round-by-round error learning for at-most-25% selections.

Train only on already-completed rounds. Freeze each round's picks before
revealing its results. Uses archived prematch probabilities, not match scores.
"""
import argparse,collections,json
from datetime import date
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scripts.second_stage_walkforward import candidate
from scripts.top25_single_pick import MARKETS,select

def run(rows,years=5,min_training=500):
    dated=[r for r in rows if r.get('date')]
    if not dated:raise ValueError('Input must contain prematch prediction dates')
    latest=max(date.fromisoformat(r['date'][:10]) for r in dated)
    start=latest.replace(year=latest.year-years) if not (latest.month==2 and latest.day==29) else latest.replace(year=latest.year-years,day=28)
    groups=collections.defaultdict(list)
    for r in dated:
        if date.fromisoformat(r['date'][:10])>=start:
            groups[(r['league'],r['season'],str(r['round']))].append(r)
    # Group by earliest date, but never reveal any match in the round until the
    # entire round is over. Same-day overlapping rounds are not trained on.
    ordered=sorted(groups.values(),key=lambda rs:(max(r['date'] for r in rs),min(r['date'] for r in rs)))
    report=[]
    # A round becomes available for learning only after its final match date.
    completed_rounds=sorted((max(r['date'] for r in group),group) for group in groups.values())
    # Only complete rounds strictly before the target round can train the model.
    for fixtures in ordered:
        kickoff=min(r['date'] for r in fixtures)
        # Strict date cutoff: no training on same-day or future outcomes.
        history=[r for finished,group in completed_rounds if finished<kickoff
                 for r in group if r.get('actual')]
        samples=[(candidate(r),r) for r in history]
        samples=[(c,r) for c,r in samples if c and c[0] in r['actual']]
        base=select(fixtures)
        result={'league':fixtures[0]['league'],'season':fixtures[0]['season'],
                'round':str(fixtures[0]['round']),'first_match':kickoff,
                'baseline':base['summary'],'training':len(samples)}
        if len(samples)>=min_training:
            x=[c[1] for c,r in samples];y=[int(bool(r['actual'][c[0]])) for c,r in samples]
            if len(set(y))==2:
                model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500)).fit(x,y)
                scored=[]
                for r in fixtures:
                    c=candidate(r)
                    if c is None:scored.append(r);continue
                    confidence=float(model.predict_proba([c[1]])[0][1])
                    scored.append(dict(r,prob={m:(confidence if m==c[0] else 0.) for m in MARKETS}))
                challenger=select(scored)
                result['challenger']=challenger['summary']
                result['selected_ids']=[p['id'] for p in challenger['selected']]
        report.append(result)
    return {'method':'chronological per-round retraining','years':years,'rounds':report,
            'warning':'Retrospective previously inspected data; not an independent future test.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--years',type=int,default=5,choices=(2,3,5))
    a=p.parse_args()
    rows=[json.loads(line) for line in Path(a.input).read_text().splitlines() if line.strip()]
    result=run(rows,a.years)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'
')
    print('ROUNDS',len(result['rounds']),'CHALLENGER',sum('challenger' in r for r in result['rounds']))
if __name__=='__main__':main()
