"""Select at most 25% of football fixtures per league/season/round.

Exactly one of five markets per selected match: 1, X, 2, over2.5, under2.5.
Only archived prematch probabilities; never use outcomes for ranking.
"""
import argparse,collections,json,math
from pathlib import Path

MARKETS=("home","draw","away","over2.5","under2.5")

def select(rows):
    rounds=collections.defaultdict(list)
    for r in rows:
        key=(r["league"],r["season"],str(r["round"]))
        rounds[key].append(r)
    selected=[]
    stats=[]
    for key,fixtures in sorted(rounds.items()):
        unique={}
        for r in fixtures:
            mid=r["id"]
            if mid in unique:raise ValueError("duplicate fixture in round: "+mid)
            unique[mid]=r
        candidates=[]
        for r in fixtures:
            probs=r["prob"]
            if not all(k in probs and isinstance(probs[k],(int,float)) and math.isfinite(probs[k]) and 0<=probs[k]<=1 for k in MARKETS):
                continue
            market=max(MARKETS,key=lambda m:(probs[m],-MARKETS.index(m)))
            candidates.append((probs[market],r["id"],market,r))
        limit=len(fixtures)//4
        winners=sorted(candidates,key=lambda x:(-x[0],x[1]))[:limit]
        for prob,mid,market,r in winners:
            result={"id":mid,"league":key[0],"season":key[1],"round":key[2],
                    "market":market,"probability":prob}
            if "actual" in r and market in r["actual"]:
                result["correct"]=bool(r["actual"][market])
            selected.append(result)
        stats.append({"league":key[0],"season":key[1],"round":key[2],
                      "fixtures":len(fixtures),"eligible":len(candidates),"selected":len(winners),
                      "limit":limit})
    evaluated=[x for x in selected if "correct" in x]
    return {"rounds":stats,"selected":selected,"summary":{"fixtures":len(rows),
            "round_count":len(stats),"selected":len(selected),"evaluated":len(evaluated),
            "hits":sum(x["correct"] for x in evaluated),
            "hit_rate":sum(x["correct"] for x in evaluated)/len(evaluated) if evaluated else None}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="out/top25-single-pick.json")
    a=p.parse_args()
    rows=[json.loads(x) for x in Path(a.input).read_text(encoding="utf-8").splitlines() if x.strip()]
    report=select(rows)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report["summary"]))
if __name__=="__main__":main()
