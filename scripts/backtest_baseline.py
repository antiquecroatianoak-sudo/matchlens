"""Leakage-safe chronological baseline for OpenFootball JSON archives.
Usage: python scripts/backtest_baseline.py
Reads historical JSON only; never changes Supabase or publishes betting tips.
"""
import json
from collections import defaultdict, Counter
from datetime import date
from pathlib import Path

def rows():
    for file in Path("data/openfootball").glob("*.json"):
        parts=file.name.split(".")
        if len(parts)!=4: continue
        league=".".join(parts[1:3])
        try: matches=json.loads(file.read_text(encoding="utf-8"))["matches"]
        except (OSError,ValueError,KeyError): continue
        for m in matches:
            score=m.get("score", {})
            if isinstance(score,dict):
                ft=score.get("ft")
                if not isinstance(ft,list) or len(ft)!=2: continue
                goals=ft
            elif isinstance(score,list) and len(score)==2: goals=score
            else: continue
            try:
                day=date.fromisoformat(str(m["date"])[:10])
                h,a=int(goals[0]),int(goals[1])
                if h<0 or a<0: continue
                home=m.get("team1") or m.get("home")
                away=m.get("team2") or m.get("away")
                if not home or not away: continue
            except (ValueError,TypeError,KeyError): continue
            yield day,league,str(home),str(away),("H" if h>a else "A" if a>h else "D")

def main():
    matches=sorted(set(rows()))
    if len(matches)<100: raise SystemExit("Insufficient scored matches; cannot train")
    # Keep last 20% chronologically untouched; validation happens only before cutoff.
    dates=sorted(set(x[0] for x in matches))
    if len(dates)<5: raise SystemExit("Insufficient dates")
    cutoff=dates[int(len(dates)*.8)]
    train=[m for m in matches if m[0]<cutoff]
    test=[m for m in matches if m[0]>=cutoff]
    if not train or not test: raise SystemExit("Empty train/test partition")
    counts=defaultdict(Counter)
    for _,league,_,_,result in train: counts[league][result]+=1
    global_counts=Counter(m[4] for m in train)
    labels=("H","D","A")
    def probs(league):
        c=counts.get(league) or global_counts
        total=sum(c.values())+len(labels)
        return {label:(c[label]+1)/total for label in labels}
    correct=0; brier=0.; logloss=0.
    import math
    by_league=defaultdict(lambda:[0,0])
    for _,league,_,_,actual in test:
        p=probs(league)
        pred=max(labels,key=lambda label:p[label])
        correct+=pred==actual
        by_league[league][0]+=pred==actual
        by_league[league][1]+=1
        brier+=sum((p[label]-(label==actual))**2 for label in labels)
        logloss-=math.log(p[actual])
    result={"model":"league_smoothed_frequencies_baseline","train":len(train),"test":len(test),
            "test_start":str(cutoff),"accuracy":correct/len(test),
            "brier":brier/len(test),"log_loss":logloss/len(test),
            "per_league":{k:{"correct":v[0],"total":v[1],"accuracy":v[0]/v[1]} for k,v in sorted(by_league.items())}}
    Path("out").mkdir(exist_ok=True)
    Path("out/backtest_baseline.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
