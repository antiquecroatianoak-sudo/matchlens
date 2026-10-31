"""Research-only top-quarter summary from historical model predictions.

Does not claim complete-round verification: input omits unscored fixtures and
historical odds. Does not tune on final-test outcomes.
"""
import argparse
import collections
import json
from pathlib import Path

MARKETS = ("home", "draw", "away", "over2.5", "under2.5")

def evaluate(path):
    groups = collections.defaultdict(list)
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("round"):
                continue
            groups[(row["league"], row["season"], row["round"])].append(row)
    selected = []
    for key, rows in sorted(groups.items()):
        # This is an observed/scored subset, NOT proof of a complete round.
        ids = [r["id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate fixture in " + repr(key))
        cap = len(rows) // 4
        ranked = []
        for row in rows:
            market = max(MARKETS, key=lambda m: row["prob"][m])
            ranked.append((row["prob"][market], row["id"], market, row))
        ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
        selected.extend((market, row) for _, _, market, row in ranked[:cap])
    n = len(selected)
    hits = sum(row["actual"][market] for market, row in selected)
    return {
        "status": "research_only",
        "round_groups_observed": len(groups),
        "selected_observed_top_quarter": n,
        "hits": hits,
        "accuracy": hits / n if n else None,
        "selection_rule": "top 25% of observed scored fixtures by calibrated probability",
        "limitations": [
            "Not a certified 25% of all scheduled fixtures; missing/postponed fixtures excluded.",
            "Historical snapshots are retrospective; not independently archived prematch forecasts.",
            "No historical bookmaker odds or 11 verified prematch factors.",
            "Previously inspected final-test seasons cannot be used again for unbiased tuning.",
            "This is evaluation only; it does not update model weights or publish tips."
        ]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = evaluate(args.predictions)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
