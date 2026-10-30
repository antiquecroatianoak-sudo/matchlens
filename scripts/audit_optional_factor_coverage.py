"""Audit evidence for eight optional MatchLens factor groups, without inventing coverage.

Usage: python scripts/audit_optional_factor_coverage.py --fixtures FILE.jsonl --output REPORT.json
Each fixture may have joined optional data and provenance. Data count as pre-match
only when explicitly marked available before kickoff.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

GROUPS = {
    "weather": ("weather",),
    "injuries": ("injuries",),
    "lineups": ("lineups",),
    "tactics": ("tactics",),
    "player_stats": ("player_stats",),
    "xg": ("xg",),
    "odds": ("odds",),
    "pitch": ("pitch",),
}
START, END = "2024-10-30", "2026-10-30"

def audit(rows):
    selected = [r for r in rows if START <= str(r.get("date", ""))[:10] <= END]
    result = {"window": [START, END], "fixtures": len(selected), "groups": {}}
    for group, (key,) in GROUPS.items():
        counts = Counter()
        for row in selected:
            value = row.get(key)
            if not value:
                counts["missing"] += 1
                continue
            counts["present"] += 1
            if isinstance(value, dict) and value.get("available_before_kickoff") is True and value.get("source_url"):
                counts["verified_prematch"] += 1
            else:
                counts["unverified_timing_or_source"] += 1
        result["groups"][group] = dict(counts)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.fixtures).read_text(encoding="utf-8").splitlines() if line.strip()]
    report = audit(rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))

if __name__ == "__main__":
    main()
