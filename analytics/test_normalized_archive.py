"""Conservative date-only historical test: no same-day results or odds.
This is an exploratory results-derived model, NOT a full-factor validation.
"""
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"data/normalized_archive"
MARKETS=("1","X","2","over_2_5","under_2_5")

def run():
    seasons=sorted(ROOT.glob("*.json"))
    rows=[]
    for path in seasons:
        league=path.name.rsplit("-",1)[-1].replace(".json","")
        for row in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            rows.append(dict(row,league=league,day=date.fromisoformat(row["date"])))
    rows.sort(key=lambda r:(r["day"],r["match_id"]))
    history=defaultdict(list)
    candidates=[]
    for row in rows:
        prior=[r for r in history[row["league"]] if r["day"] < row["day"]-timedelta(days=1)]
        if len(prior)>=30:
            home=[r for r in prior if r["home_team"]==row["home_team"] or r["away_team"]==row["home_team"]]
            away=[r for r in prior if r["home_team"]==row["away_team"] or r["away_team"]==row["away_team"]]
            if len(home)>=5 and len(away)>=5:
                def rates(team):
                    played=[r for r in prior if r["home_team"]==team or r["away_team"]==team][-15:]
                    scored=sum(r["home_goals"] if r["home_team"]==team else r["away_goals"] for r in played)
                    conceded=sum(r["away_goals"] if r["home_team"]==team else r["home_goals"] for r in played)
                    return ((scored+8*1.3)/(len(played)+8),(conceded+8*1.3)/(len(played)+8))
                ha,hd=rates(row["home_team"])
                aa,ad=rates(row["away_team"])
                lh=(ha*ad/1.3)*1.08
                la=(aa*hd/1.3)*0.92
                probs=[0.0]*4
                for h in range(12):
                    ph=math.exp(-lh)*lh**h/math.factorial(h)
                    for a in range(12):
                        p=ph*math.exp(-la)*la**a/math.factorial(a)
                        probs[0 if h>a else 1 if h==a else 2]+=p
                        if h+a>2: probs[3]+=p
                p1,px,p2,po=probs
                allp=(p1,px,p2,po,1-po)
                ix=max(range(5),key=lambda i:allp[i])
                h,a=row["home_goals"],row["away_goals"]
                hit=(h>a,h==a,h<a,h+a>2,h+a<=2)[ix]
                candidates.append({"match_id":row["match_id"],"league":row["league"],
                                   "date":row["date"],"market":MARKETS[ix],
                                   "confidence":allp[ix],"correct":hit})
        history[row["league"]].append(row)
    quota=len(rows)//4
    picks=sorted(candidates,key=lambda r:(-r["confidence"],r["match_id"]))[:quota]
    per_league=defaultdict(lambda:{"selected":0,"correct":0})
    for p in picks:
        per_league[p["league"]]["selected"]+=1
        per_league[p["league"]]["correct"]+=int(p["correct"])
    return {"label":"EXPLORATORY RESULTS-ONLY DATE-SAFE TEST, NOT FULL-FACTOR",
            "matches":len(rows),"leagues":len({r["league"] for r in rows}),
            "eligible":len(candidates),"global_quota":quota,
            "selected":len(picks),"correct":sum(p["correct"] for p in picks),
            "hit_rate":sum(p["correct"] for p in picks)/len(picks) if picks else None,
            "by_league":dict(sorted(per_league.items())),
            "limitations":"No archived prematch factors; same-day and previous-day results excluded; selection uses full-period confidence ranking and is retrospective.",
            "predictions":picks}

if __name__=="__main__":
    result=run()
    print(json.dumps({k:v for k,v in result.items() if k!="predictions"},ensure_ascii=False,indent=2))
