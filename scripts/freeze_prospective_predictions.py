"""Freeze prospective baseline predictions and rank the strongest 25% per round.

This is an immutable-in-run research snapshot, not database persistence.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

def select(rows, created_at):
    groups = {}
    for row in rows:
        kickoff = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
        if kickoff <= created_at:
            continue
        probs = row["prob"]
        if isinstance(probs, dict):
            candidates = [(k, float(probs[k])) for k in ("home","draw","away") if k in probs]
        else:
            candidates = []  # Only explicit 1X2 market labels are supported.
        if not candidates or not all(math.isfinite(v) and 0 <= v <= 1 for _, v in candidates):
            continue
        outcome, confidence = max(candidates, key=lambda kv: kv[1])
        record = {**row, "predicted_outcome": outcome, "confidence": confidence,
                  "predicted_at_utc": created_at.isoformat(),
                  "selection_rule": "top_25_percent_per_league_round"}
        groups.setdefault((row["league"], row["season"], row["round"]), []).append(record)
    all_rows = []
    for group in groups.values():
        group.sort(key=lambda r: (-r["confidence"], r["kickoff_utc"], r["id"]))
        count = 0  # No Top 25 publication without independently certified complete round.
        for index, row in enumerate(group):
            row["top25"] = index < count
            row["selection_group_size"] = len(group)
            all_rows.append(row)
    return all_rows

def main():
    path = Path("out/upcoming-probabilities.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    created_at = datetime.now(timezone.utc)
    selected = select(rows, created_at)
    out = Path("out/prospective-predictions.jsonl")
    out.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected))
    summary = {"generated_at_utc": created_at.isoformat(), "scored": len(rows),
               "eligible": len(selected), "top25": sum(r["top25"] for r in selected),
               "warning": "Research only. Top25 disabled until independently certified complete rounds; no durable database persistence."}
    Path("out/prospective-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("PROSPECTIVE SNAPSHOT", summary)

if __name__ == "__main__":
    main()
