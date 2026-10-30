"""Leakage-safe chronological walk-forward Elo sensitivity research.

Runs on isolated 34-match StatsBomb sample. Not an independent or representative test.
"""
import argparse, json, math
from collections import defaultdict
from pathlib import Path

def simulate(matches, home_adv, k, warmup):
    ratings=defaultdict(lambda:1500.0)
    picks=[]
    for i,m in enumerate(matches):
        h,a=m["home_id"],m["away_id"]
        p=1/(1+10**((ratings[a]-ratings[h]-home_adv)/400))
        outcome=1 if m["home_goals"]>m["away_goals"] else (.5 if m["home_goals"]==m["away_goals"] else 0)
        if i>=warmup:
            pick="home" if p>=.5 else "away"
            hit=(pick=="home" and outcome==1) or (pick=="away" and outcome==0)
            picks.append({"id":m["match_id"],"date":m["date"],"pick":pick,"correct":bool(hit),"p_home":p})
        delta=k*(outcome-p)
        ratings[h]+=delta
        ratings[a]-=delta
    return picks

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/research/statsbomb_bundesliga_2023_24_sample.json")
    p.add_argument("--output",default="out/elo_sensitivity.json")
    args=p.parse_args()
    matches=json.loads(Path(args.source).read_text(encoding="utf-8"))["matches"]
    matches.sort(key=lambda m:(m["date"],m["match_id"]))
    results=[]
    for home_adv in [0,40,65,90]:
        for k in [10,20,30]:
            picks=simulate(matches,home_adv,k,10)
            results.append({"home_adv":home_adv,"k":k,"n":len(picks),
                            "hits":sum(x["correct"] for x in picks),
                            "accuracy":sum(x["correct"] for x in picks)/len(picks) if picks else None})
    baseline=simulate(matches,65,20,10)
    assert len(matches)==34 and len(baseline)==24
    output={"source_matches":len(matches),"combinations":results,
            "baseline_predictions":baseline,
            "caution":"All 12 variants evaluated on the SAME small incomplete sample. No independent validation, no production tuning, no league-round selection, no bookmaker odds. Do not select a winner as a verified improvement."}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"combinations":len(results),"matches":len(matches),"baseline_hits":sum(x["correct"] for x in baseline)}))

if __name__=="__main__":main()
