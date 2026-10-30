"""Chronological Elo 1X2 backtest; evaluates only matches after the baseline cutoff."""
import json, math
from collections import defaultdict
from datetime import date
from pathlib import Path
from backtest_baseline import rows

LABELS=("H","D","A")
def main():
    matches=sorted(set(rows()))
    dates=sorted({m[0] for m in matches})
    if len(matches)<100 or len(dates)<5:
        raise SystemExit("Insufficient history")
    cutoff=dates[int(len(dates)*.8)]
    # Same-day fixtures must not update one another before predictions.
    rating=defaultdict(lambda:1500.0)
    stats={str(k):{"correct":0,"n":0,"brier":0.0,"log_loss":0.0} for k in (0,40,65,90,120)}
    for day in dates:
        day_matches=[m for m in matches if m[0]==day]
        updates=[]
        for _,league,home,away,outcome in day_matches:
            h=(league,home); a=(league,away)
            diff=rating[h]-rating[a]
            for advantage in (0,40,65,90,120):
                expected=1/(1+10**(-(diff+advantage)/400))
                # Draw probability peaks at even strength; normalized 1X2.
                draw=0.27*math.exp(-abs(diff+advantage)/700)
                p={"H":expected*(1-draw),"D":draw,"A":(1-expected)*(1-draw)}
                if day>=cutoff:
                    s=stats[str(advantage)]
                    s["n"]+=1
                    s["correct"]+=max(LABELS,key=lambda x:p[x])==outcome
                    s["brier"]+=sum((p[x]-(x==outcome))**2 for x in LABELS)
                    s["log_loss"]-=math.log(max(p[outcome],1e-12))
            expected=1/(1+10**(-(diff+65)/400))
            actual={"H":1,"D":0.5,"A":0}[outcome]
            delta=20*(actual-expected)
            updates.append((h,a,delta))
        for h,a,delta in updates:
            rating[h]+=delta;rating[a]-=delta
    results={k:{"accuracy":v["correct"]/v["n"],"test":v["n"],"brier":v["brier"]/v["n"],"log_loss":v["log_loss"]/v["n"]} for k,v in stats.items() if v["n"]}
    output={"model":"elo_home_advantage_sweep","test_start":str(cutoff),"note":"Exploratory test-set sweep only; select hyperparameters on a separate validation period before claiming out-of-sample improvement.","results":results}
    Path("out").mkdir(exist_ok=True)
    Path("out/backtest_elo.json").write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))
if __name__=="__main__":main()
