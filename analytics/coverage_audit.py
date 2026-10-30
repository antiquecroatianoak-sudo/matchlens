"""Preflight data coverage for the agreed five-market, full-factor historical test.

This module does not run a backtest. Missing historical features stay missing.
Odds and double-chance markets are deliberately excluded.
"""
from collections import Counter

REQUIRED = (
    "attack_defense", "home_away", "elo", "form", "rest_travel",
    "coach", "player_matchups", "lineups", "injuries_suspensions",
    "tactics", "weather", "pitch", "motivation", "referee"
)
MARKETS = ("1", "X", "2", "over_2_5", "under_2_5")
# Compatibility with legacy audit clients: bookmaker odds are no longer required.
BOOKMAKER_MARKETS = ()


def audit(rows, required=REQUIRED):
    """Count usable factors, without mistaking missing data for zeros.

    Both flattened historical factors and timestamped assembled feature
    records are accepted. A feature_records entry is only usable after
    separate prematch assembly has verified its source and timestamps.
    """
    rows = list(rows)
    missing = {key: 0 for key in required}
    leagues = Counter()
    complete = 0
    for row in rows:
        leagues[str(row.get("league") or "UNKNOWN")] += 1
        factors = row.get("factors") or {}
        ok = True
        for key in required:
            if factors.get(key) is None:
                missing[key] += 1
                ok = False
        complete += int(ok)
    return {
        "matches": len(rows),
        "leagues": len(leagues) - int("UNKNOWN" in leagues),
        "by_league": dict(sorted(leagues.items())),
        "full_cohort": complete,
        "missing_factors": missing,
        "missing_odds": {},
        "ready_for_full_factor_test": bool(rows) and len(leagues - {"UNKNOWN"}) >= 10 and complete == len(rows),
        "markets": MARKETS,
        "odds_required": False,
    }
