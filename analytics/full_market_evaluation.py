"""Joint evaluation of all requested football markets, without fabricated odds.

Each row must contain actual result, pre-kickoff probabilities and dated bookmaker
prices. Missing odds or any required factor exclude the row from the FULL-data cohort.
This is evaluation infrastructure, not a trained multi-factor predictor.
"""
import math
from datetime import datetime, timezone

MARKETS = ("1", "X", "2", "over_2_5", "under_2_5", "1X", "X2")

def instant(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)

def evaluate(rows, required_factors=()):
    results = {m: {"eligible": 0, "correct": 0, "profit_units": 0., "brier_sum": 0.} for m in MARKETS}
    exclusions = {"missing_factor": 0, "missing_or_late_odds": 0}
    for r in rows:
        cutoff = instant(r["prediction_at"])
        if cutoff >= instant(r["kickoff"]):
            raise ValueError("Prediction cannot occur at or after kickoff")
        if any(r.get("factors", {}).get(f) is None for f in required_factors):
            exclusions["missing_factor"] += 1
            continue
        probs = r["probabilities"]
        p1, px, p2, po = (probs[k] for k in ("1", "X", "2", "over_2_5"))
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or not 0 <= v <= 1 for v in (p1, px, p2, po)) or abs(p1 + px + p2 - 1) > 1e-6:
            raise ValueError("Invalid probabilities")
        h, a = r["home_goals"], r["away_goals"]
        truth = {"1": h > a, "X": h == a, "2": h < a, "over_2_5": h+a > 2, "under_2_5": h+a < 3, "1X": h >= a, "X2": h <= a}
        pred = {"1": p1, "X": px, "2": p2, "over_2_5": po, "under_2_5": 1-po, "1X": p1+px, "X2": px+p2}
        for market in MARKETS:
            quote = r.get("odds", {}).get(market)
            synthetic = market in ("1X", "X2")
            if synthetic:
                fair_p = pred[market]
                quote = {"price": 1 / fair_p, "available_at": r["prediction_at"]} if fair_p > 0 else None
            if not quote or not isinstance(quote.get("price"), (int,float)) or isinstance(quote.get("price"), bool) or not math.isfinite(quote["price"]) or quote["price"] <= 1 or instant(quote["available_at"]) > cutoff:
                exclusions["missing_or_late_odds"] += 1
                continue
            if market in ("1X", "X2") and quote["price"] <= 2:
                continue
            x = results[market]
            x["eligible"] += 1
            x["correct"] += int(truth[market])
            if market not in ("1X", "X2"):
                x["profit_units"] += (quote["price"]-1 if truth[market] else -1)
            x["brier_sum"] += (pred[market] - int(truth[market]))**2
    for v in results.values():
        n = v["eligible"]
        v["accuracy"] = v["correct"]/n if n else None
        v["brier"] = v.pop("brier_sum")/n if n else None
        v["profit_units"] = None if v is results["1X"] or v is results["X2"] else round(v["profit_units"], 6)
    return {"markets": results, "exclusions": exclusions, "required_factors": list(required_factors), "synthetic_double_chance": "fair implied 1/p, no bookmaker margin, no realizable ROI"}
