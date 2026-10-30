"""Global top-25% selection across every imported match, never per league.

Exploratory result-only model; no odds and no 1X/X2. A full-factor test
requires additional time-stamped features and more league datasets.
"""
import json
from pathlib import Path
from analytics.historical_baseline import walk_forward

ROOT=Path(__file__).resolve().parents[1]/"data"/"openfootball"
FILES=("en_2023_24.json","en_2024_25.json","2024-25_de.1.json",
       "2024-25_es.1.json","2024-25_it.1.json","2024-25_fr.1.json")
MARKETS=("1","X","2","over_2_5","under_2_5")

def run():
    all_matches=[]
    candidates=[]
    league_stats={}
    for filename in FILES:
        payload=json.loads((ROOT/filename).read_text(encoding="utf-8"))
        rows=payload["matches"]
        all_matches.extend(rows)
        league=payload["league"]
        league_stats.setdefault(league,{"matches":0,"selected":0,"correct":0})
        league_stats[league]["matches"]+=len(rows)
        # Historical training is league-specific; global ranking is NOT.
        predictions=walk_forward(rows,min_history=10,delay_days=2)["predictions"]
        by_id={r["match_id"]:r for r in rows}
        for p in predictions:
            m=by_id[p["match_id"]]
            if m.get("home_goals") is None or m.get("away_goals") is None: continue
            p1,px,p2=p["probabilities_1x2"]
            po=p["probability_over25"]
            probs=(p1,px,p2,po,1-po)
            index=max(range(5),key=lambda k:probs[k])
            candidates.append({"match_id":m["match_id"],"league":league,
                               "market":MARKETS[index],"confidence":probs[index],
                               "home_goals":m["home_goals"],"away_goals":m["away_goals"]})
    # Exactly one global quota. A league may contribute zero or all selected games.
    quota=(len(all_matches)+2)//4
    picks=sorted(candidates,key=lambda r:(-r["confidence"],r["match_id"]))[:quota]
    for p in picks:
        h,a=p["home_goals"],p["away_goals"]
        hit={"1":h>a,"X":h==a,"2":h<a,"over_2_5":h+a>2,"under_2_5":h+a<=2}[p["market"]]
        p["correct"]=hit
        league_stats[p["league"]]["selected"]+=1
        league_stats[p["league"]]["correct"]+=int(hit)
    return {"method":"global top-25% five-market result-only exploratory baseline",
            "total_matches":len(all_matches),"eligible":len(candidates),
            "global_quota":quota,"selected":len(picks),
            "correct":sum(p["correct"] for p in picks),
            "accuracy":sum(p["correct"] for p in picks)/len(picks) if picks else None,
            "by_league":league_stats,
            "limitations":"Only 5 leagues/6 season-files currently verified; not 10+. Date-only kickoff placeholders; no full historical context, calibration or truly prospective validation."}

if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
