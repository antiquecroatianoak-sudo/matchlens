"""Leakage-safe evaluation of top-quarter football predictions.

Input CSV columns: kickoff, league, season, round, match_id, predicted_probability,
actual_correct, valid_parameters. Predictions must have been generated before kickoff.
Usage: python scripts/evaluate_top25.py predictions.csv
"""
import csv
import math
import sys
from collections import defaultdict
from datetime import datetime

def evaluate(path):
    groups = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            p = float(row["predicted_probability"])
            n = int(row["valid_parameters"])
            if not 0 <= p <= 1 or n < 11:
                continue
            datetime.fromisoformat(row["kickoff"].replace("Z", "+00:00"))
            key = (row["league"], row["season"], row["round"])
            groups[key].append(row)
    selected = []
    for key, matches in groups.items():
        # A full round must be independently confirmed before selection.
        # Never infer completeness from the observed number of rows.
        if not all(r.get("round_complete", "").lower() == "true" for r in matches):
            continue
        unique = {}
        for row in matches:
            mid = row["match_id"]
            if mid in unique:
                raise ValueError(f"Duplicate match {mid} in {key}")
            unique[mid] = row
        limit = math.floor(len(unique) * 0.25)
        ranked = sorted(unique.values(), key=lambda r: float(r["predicted_probability"]), reverse=True)
        selected.extend(ranked[:limit])
    if not selected:
        raise ValueError("No eligible predictions in complete rounds")
    hits = sum(int(r["actual_correct"]) for r in selected)
    print(f"selected={len(selected)} hits={hits} accuracy={hits/len(selected):.4%}")
    print("Research metric only; requires strictly out-of-time predictions and locked holdout.")

if __name__ == "__main__":
    evaluate(sys.argv[1])
