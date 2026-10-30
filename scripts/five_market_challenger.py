"""Five-market chronological challenger. Research only; no outcome leakage."""
import argparse, collections, json, math
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scripts.top25_single_pick import MARKETS, select

def valid(row):
    p=row.get("prob", {})
    return all(isinstance(p.get(m),(int,float)) and math.isfinite(p[m]) and 0<=p[m]<=1 for m in MARKETS)

def features(row, market):
    p=row["prob"]
    peers=MARKETS[:3] if market in MARKETS[:3] else MARKETS[3:]
    # All additional factors use only pre-match model probabilities, never outcomes.
    outcome=[p[m] for m in MARKETS[:3]]
    goals=[p[m] for m in MARKETS[3:]]
    eps=1e-9
    entropy=-sum(v*math.log(max(v,eps)) for v in outcome)
    sorted_outcome=sorted(outcome,reverse=True)
    margin=sorted_outcome[0]-sorted_outcome[1]
    goal_balance=abs(goals[0]-goals[1])
    chosen=p[market]
    return [chosen, chosen-max(p[m] for m in peers if m!=market),
            max(outcome),max(goals),entropy,margin,goal_balance,
            outcome[0]-outcome[2],outcome[1],
            sum(v*v for v in outcome),
            -math.log(max(1-chosen,eps)),
            chosen*(1-chosen)] + [int(m==market) for m in MARKETS]

def run(rows, min_training=500):
    groups=collections.defaultdict(list)
    for r in rows:
        if r.get("date"):
            groups[(r["league"],str(r["season"]),str(r["round"]))].append(r)
    ordered=sorted(groups.values(),key=lambda g:(min(r["date"] for r in g),str(g[0]["league"]),str(g[0]["round"])))
    results=[]
    for group in ordered:
        start=min(r["date"] for r in group)
        history=[r for past in ordered if max(x["date"] for x in past)<start for r in past if valid(r) and isinstance(r.get("actual"),dict)]
        X=[]; y=[]
        for r in history:
            for market in MARKETS:
                if market in r["actual"]:
                    X.append(features(r,market))
                    y.append(int(bool(r["actual"][market])))
        baseline=select(group)
        entry={"league":group[0]["league"],"season":group[0]["season"],"round":str(group[0]["round"]),
               "start":start,"training_fixtures":len(history),"training_labels":len(y),
               "baseline":baseline["summary"]}
        if len(history)>=min_training and len(set(y))==2:
            model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500))
            model.fit(X,y)
            scored=[]
            for r in group:
                if not valid(r):
                    scored.append(r)
                    continue
                scores=model.predict_proba([features(r,m) for m in MARKETS])[:,1]
                scored.append(dict(r,prob={m:float(scores[i]) for i,m in enumerate(MARKETS)}))
            challenger=select(scored)
            entry["challenger"]=challenger["summary"]
            entry["baseline_picks"]=baseline["selected"]
            entry["challenger_picks"]=challenger["selected"]
        results.append(entry)
    return {"method":"five-market expanding chronological ranking","rounds":results,
            "warning":"Retrospective archive; previously inspected seasons are not a pristine holdout."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--min-training",type=int,default=500)
    a=p.parse_args()
    rows=[json.loads(line) for line in Path(a.input).read_text().splitlines() if line.strip()]
    result=run(rows,a.min_training)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    for name in ("baseline","challenger"):
        entries=[r[name] for r in result["rounds"] if "challenger" in r]
        hits=sum(x["hits"] for x in entries); evaluated=sum(x["evaluated"] for x in entries)
        print(name,hits,evaluated,hits/evaluated if evaluated else None)
if __name__=="__main__": main()
