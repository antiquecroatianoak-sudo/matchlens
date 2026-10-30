"""Single combined MatchLens selection: one tip for 25% of each round."""
from math import ceil, floor, isfinite

REGULAR=("1","X","2","over_2_5","under_2_5")
SYNTHETIC=("1X","X2")

def choose_round(matches):
    """Each match: id, probabilities (1,X,2,over_2_5), odds with price+available_at,
    prediction_at. A quote after prediction_at is ineligible.
    Round quota is round-half-up(25%), minimum 1 if nonempty.
    Returns selected picks, including empty list when no eligible match.
    """
    candidates=[]
    for match in matches:
        p=match["probabilities"]
        p1,px,p2,po=(p[k] for k in ("1","X","2","over_2_5"))
        vals=(p1,px,p2,po)
        if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and isfinite(v) and 0<=v<=1 for v in vals) or abs(p1+px+p2-1)>1e-6:
            raise ValueError("Invalid probabilities")
        probs={"1":p1,"X":px,"2":p2,"over_2_5":po,"under_2_5":1-po,"1X":p1+px,"X2":px+p2}
        valid=[]
        for market in REGULAR:
            quote=match.get("odds",{}).get(market)
            if quote and isinstance(quote.get("price"),(int,float)) and not isinstance(quote["price"],bool) and isfinite(quote["price"]) and quote["price"]>1.30 and quote.get("available_at") and quote["available_at"]<=match["prediction_at"]:
                valid.append((market,probs[market],quote["price"]))
        for market in SYNTHETIC:
            probability=probs[market]
            if probability>0 and 1/probability>2:
                valid.append((market,probability,1/probability))
        if valid:
            market,probability,price=max(valid,key=lambda v:(v[1],v[0]))
            candidates.append({"match_id":match["match_id"],"market":market,"probability":probability,"odds":price,"synthetic":market in SYNTHETIC})
    count=max(1,floor(len(matches)*.25+.5)) if matches else 0
    return sorted(candidates,key=lambda v:(-v["probability"],v["match_id"]))[:count]

def backtest(rounds):
    """Round dicts with matches; each match also has home_goals and away_goals."""
    chosen=[]
    for round_data in rounds:
        picks=choose_round(round_data["matches"])
        truth={m["match_id"]:m for m in round_data["matches"]}
        for pick in picks:
            m=truth[pick["match_id"]];h,a=m["home_goals"],m["away_goals"]
            outcomes={"1":h>a,"X":h==a,"2":h<a,"over_2_5":h+a>2,"under_2_5":h+a<=2,"1X":h>=a,"X2":h<=a}
            chosen.append({**pick,"round_id":round_data["round_id"],"correct":outcomes[pick["market"]]})
    n=len(chosen)
    return {"rounds":len(rounds),"selected":n,"correct":sum(p["correct"] for p in chosen),"accuracy":sum(p["correct"] for p in chosen)/n if n else None,"picks":chosen}
