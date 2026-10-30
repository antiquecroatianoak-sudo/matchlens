"""Top-quarter confidence audit on the existing calibrated MatchLens Poisson/Elo-era baseline.

Research only. Historical audit seasons were previously inspected; not a new
independent out-of-sample claim. No training or selection uses test outcomes.
Run: python -m analytics.top_quarter_audit --data data/openfootball
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from analytics.backtest import load_matches, walk, fit_calibration, apply_calibration, SPLITS

MARKETS = ("home", "draw", "away", "over2.5", "under2.5")


def pick(row):
    """Exactly one highest-probability market per match; deterministic ties."""
    market = max(MARKETS, key=lambda k: row["prob"][k])
    return {"id": row["id"], "date": row["date"], "season": row["season"],
            "league": row["league"], "market": market,
            "confidence": row["prob"][market],
            "hit": int(row["actual"][market])}


def summarize(picks):
    n = len(picks)
    if not n:
        return {"selected": 0, "hits": 0, "misses": 0, "accuracy": None}
    hits = sum(p["hit"] for p in picks)
    return {"selected": n, "hits": hits, "misses": n-hits,
            "accuracy": hits/n,
            "mean_confidence": sum(p["confidence"] for p in picks)/n,
            "brier": sum((p["confidence"]-p["hit"])**2 for p in picks)/n,
            "log_loss": -sum(p["hit"]*math.log(max(1e-12,p["confidence"])) +
                              (1-p["hit"])*math.log(max(1e-12,1-p["confidence"]))
                              for p in picks)/n}


def audit(rows, fraction=.25):
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    # Fixed configuration from archived 27-candidate tuning, not chosen on audit.
    config = {"window": 50, "half_life": 30, "prior": 8}
    predictions = walk(rows, config)
    calibration = [r for r in predictions if r["season"] in SPLITS["calibration"]]
    test = [r for r in predictions if r["season"] in SPLITS["test"]]
    if not calibration or not test:
        raise ValueError("Missing calibration or audit seasons")
    calibrated = apply_calibration(test, fit_calibration(calibration))
    pool = [pick(r) for r in calibrated]
    # Rank every eligible match before looking at its actual result. Ties use ID.
    ranked = sorted(pool, key=lambda p: (-p["confidence"], p["id"]))
    count = max(1, math.ceil(len(ranked)*fraction))
    chosen = ranked[:count]
    leagues = sorted({p["league"] for p in pool})
    return {
        "protocol": "top-quarter-single-market-v1",
        "status": "retrospective_previously_viewed_seasons_not_independent",
        "model": "existing_poisson_calibrated_archived_configuration",
        "fraction": fraction,
        "ranking": "highest calibrated market probability, deterministic match ID ties",
        "one_pick_per_match": True,
        "configuration": config,
        "audit_seasons": SPLITS["test"],
        "eligible_matches": len(pool),
        "all_matches": summarize(pool),
        "top_quarter": summarize(chosen),
        "by_season": {s: summarize([p for p in chosen if p["season"] == s])
                      for s in SPLITS["test"]},
        "by_league": {league: summarize([p for p in chosen if p["league"] == league])
                      for league in leagues},
        "by_market": {market: summarize([p for p in chosen if p["market"] == market])
                      for market in MARKETS},
        "selected_ids": [p["id"] for p in chosen],
        "limitations": [
            "Previously inspected audit seasons; descriptive, not prospective validation.",
            "Top quarter is global over the audit period, not daily Top 25%.",
            "One strongest offer per match, not all five offers.",
            "Historical schedule and available features are retrospective snapshots.",
            "No timestamped odds; hit rate is not betting profitability.",
            "No self-modifying live model or new coach/player features are implied."
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/openfootball")
    parser.add_argument("--out", default="out/top_quarter_audit.json")
    args = parser.parse_args()
    rows, _ = load_matches(args.data)
    result = audit(rows)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "selected_ids"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
