"""Audit whether a dataset can support the requested all-factor, seven-market test.

Never invent historical odds or fill unavailable factors with zero.
"""
from analytics.full_market_evaluation import MARKETS

REQUIRED = (
    "attack_defense", "home_away", "elo", "form", "rest_travel",
    "coach", "player_matchups", "lineups", "injuries_suspensions",
    "tactics", "weather", "pitch", "motivation", "referee"
)

def audit(rows, required=REQUIRED):
    missing = {key: 0 for key in required}
    missing_odds = {market: 0 for market in MARKETS}
    eligible = 0
    for row in rows:
        factors = row.get("factors") or {}
        odds = row.get("odds") or {}
        complete_factors = True
        complete_odds = True
        for key in required:
            if factors.get(key) is None:
                missing[key] += 1
                complete_factors = False
        for market in MARKETS:
            if odds.get(market) is None:
                missing_odds[market] += 1
                complete_odds = False
        if complete_factors and complete_odds:
            eligible += 1
    return {"matches": len(rows), "full_cohort": eligible,
            "missing_factors": missing, "missing_odds": missing_odds}
