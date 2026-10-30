"""Five-market, no-odds exploratory walk-forward backtest across imported leagues.

This is NOT the full-factor MatchLens model. Dates are placeholders, and blocks
of 10/9 matches proxy rounds because source files lack verified round IDs.
"""
import json
from collections import defaultdict
from pathlib import Path
from analytics.historical_baseline import walk_forward

ROOT=Path(__file__).resolve().parents[1]/"data"/"openfootball"
FILES=("en_2023_24.json","en_2024_25.json","2024-25_de.1.json",
       "2024-25_es.1.json","2024-25_it.1.json","2024-25_fr.1.json")
MARKETS=("1","X","2","over_2_5","under_2_5")

def run():
    total=correct=0
    detail=[]
    for filename in FILES:
        payload=json.loads((ROOT/filename).read_text(encoding="utf-8"))
        rows=payload["matches"]
        # Per-league history only. Date-only snapshots have assumed 2-day result delay.
        predictions=walk_forward(rows,min_history=10,delay_days=2)["predictions"]
        lookup={r["match_id"]:r for r in rows}
        predicted={p["match_id"]:p for p in predictions}
        # Fixed-size chronological blocks are an approximation, NOT verified rounds.
        ordered=sorted(rows,key=lambda r:(r["kickoff"],r["match_id"]))
        block_size=9 if payload["league"] in ("Bundesliga","Ligue 1") else 10
        league_selected=league_correct=0
        for i in range(0,len(ordered),block_size):
            block=ordered[i:i+block_size]
            candidates=[]
            for m in block:
                p=predicted.get(m["match_id"])
                if not p: continue
                p1,px,p2=p["probabilities_1x2"]
                po=p["probability_over25"]
                probs=(p1,px,p2,po,1-po)
                idx=max(range(5),key=lambda k:probs[k])
                candidates.append((probs[idx],m["match_id"],MARKETS[idx],m))
            # Round-half-up 25% of ALL matches in block, not only eligible.
            quota=(len(block)+2)//4
            for _,_,market,m in sorted(candidates,key=lambda x:(-x[0],x[1]))[:quota]:
                h,a=m["home_goals"],m["away_goals"]
                hit={"1":h>a,"X":h==a,"2":h<a,"over_2_5":h+a>2,"under_2_5":h+a<=2}[market]
                league_selected+=1
                league_correct+=int(hit)
        total+=league_selected;correct+=league_correct
        detail.append({"file":filename,"league":payload["league"],"matches":len(rows),
                       "selected":league_selected,"correct":league_correct,
                       "accuracy":league_correct/league_selected if league_selected else None})
    return {"method":"exploratory five-market baseline; no odds; no 1X/X2",
            "rounds":"chronological fixed-size blocks; NOT official rounds",
            "selected":total,"correct":correct,"accuracy":correct/total if total else None,
            "leagues":detail,
            "limitations":"Result-only Poisson baseline; missing extra factors; date-only kickoff placeholders; seasons used in development."}

if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
