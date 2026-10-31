"""Compare frozen top-quarter predictions against missed winners in the remaining 75%.

Research only: comparisons are retrospective diagnostics, never hindsight swaps.
"""
import argparse
import collections
import json
from pathlib import Path

MARKETS=("home","draw","away","over2.5","under2.5")

def audit(path):
    groups=collections.defaultdict(list)
    with open(path,encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            r=json.loads(line)
            if r.get("round"): groups[(r["league"],r["season"],r["round"])].append(r)
    totals=collections.Counter()
    by_market=collections.defaultdict(collections.Counter)
    by_league=collections.defaultdict(collections.Counter)
    for key,group in sorted(groups.items()):
        if len({r["id"] for r in group})!=len(group):
            raise ValueError("Duplicate match in "+repr(key))
        candidates=[]
        for r in group:
            market=max(MARKETS,key=lambda m:r["prob"][m])
            candidates.append((float(r["prob"][market]),str(r["id"]),market,r))
        candidates.sort(key=lambda x:(-x[0],x[1],x[2]))
        n=len(candidates)//4
        for idx,(_,_,market,r) in enumerate(candidates):
            chosen=idx<n
            hit=int(r["actual"][market])
            key_name="selected" if chosen else "not_selected"
            totals[key_name]+=1
            totals[key_name+"_hits"]+=hit
            by_market[market][key_name]+=1
            by_market[market][key_name+"_hits"]+=hit
            by_league[r["league"]][key_name]+=1
            by_league[r["league"]][key_name+"_hits"]+=hit
    return {
      "status":"research_only",
      "totals":dict(totals),
      "by_market":{k:dict(v) for k,v in sorted(by_market.items())},
      "by_league":{k:dict(v) for k,v in sorted(by_league.items())},
      "diagnostic":"Count hits outside the selected quarter and misses inside it; use earlier data to train a new ranking model, then evaluate on genuinely unseen future rounds.",
      "limitations":"The actual winning bets among excluded matches are only known after kickoff. Hindsight swaps are not valid prematch predictions. The source lacks certified complete rounds, verified 11 factors and historical executable odds."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("predictions")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=audit(a.predictions)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
