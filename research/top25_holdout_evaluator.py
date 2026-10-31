"""Leakage-aware evaluation of a fixed top-quarter selection policy.

Input JSONL rows: fixture_id, league, season, round, kickoff, generated_at,
market, selection, probability, outcome (0/1), model_version.
Only use this on a held-out period after model selection.
"""
import argparse
import collections
import datetime as dt
import json
import math

def evaluate(rows):
    groups = collections.defaultdict(list)
    seen = set()
    for r in rows:
        key = (r["league"], r["season"], r["round"])
        identity = (r["fixture_id"], r["market"], r["selection"])
        if (key, identity) in seen:
            raise ValueError("duplicate prediction")
        seen.add((key, identity))
        if dt.datetime.fromisoformat(r["generated_at"].replace("Z", "+00:00")) >= dt.datetime.fromisoformat(r["kickoff"].replace("Z", "+00:00")):
            raise ValueError("prediction generated at/after kickoff")
        p = float(r["probability"])
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("invalid probability")
        if r["outcome"] not in (0, 1):
            raise ValueError("outcome must be binary")
        groups[key].append(r)
    selected = []
    for key, group in groups.items():
        # This file expects all fixtures of a round, including those without a pick.
        fixture_ids = {r["fixture_id"] for r in group}
        cap = len(fixture_ids) // 4
        if cap == 0:
            continue
        ranked = sorted(group, key=lambda r: (-float(r["probability"]), str(r["fixture_id"]), str(r["market"]), str(r["selection"])))
        chosen = set()
        for r in ranked:
            if len(chosen) >= cap:
                break
            if r["fixture_id"] in chosen:
                continue
            chosen.add(r["fixture_id"])
            selected.append(r)
    hits = sum(r["outcome"] for r in selected)
    n = len(selected)
    return {"rounds": len(groups), "selected": n, "hits": hits,
            "accuracy": hits / n if n else None,
            "warning": "Input must contain the complete fixture list for every round; otherwise the 25% cap is not certified."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions_jsonl")
    args = parser.parse_args()
    with open(args.predictions_jsonl, encoding="utf-8") as f:
        print(json.dumps(evaluate(json.loads(line) for line in f if line.strip()), indent=2))
