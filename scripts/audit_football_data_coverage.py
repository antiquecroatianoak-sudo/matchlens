"""Audit staged football-data.org coverage against a canonical fixture JSONL.

Strict matching on UTC calendar date and normalized team names; ambiguous
matches are rejected. This is a coverage audit, not proof of venue identity.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def read(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(canonical, staged):
    index = defaultdict(list)
    for row in staged:
        day = str(row.get("kickoff_utc", ""))[:10]
        if not day:
            continue
        index[(day, norm(row.get("home")), norm(row.get("away")))].append(row)
    matched, unresolved = [], []
    for row in canonical:
        day = str(row.get("date", ""))[:10]
        if not ("2024-10-30" <= day <= "2026-10-30"):
            continue
        key = (day, norm(row.get("home")), norm(row.get("away")))
        options = index.get(key, [])
        if len(options) == 1:
            source = options[0]
            matched.append({"id": row.get("id"), "provider_id": source.get("provider_id"),
                            "kickoff_utc": source["kickoff_utc"],
                            "source_url": source.get("source_url"),
                            "verified_venue": None})
        else:
            unresolved.append({"id": row.get("id"), "reason": "ambiguous" if options else "no_exact_match"})
    return matched, unresolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--staged", required=True)
    parser.add_argument("--matched", required=True)
    parser.add_argument("--unresolved", required=True)
    args = parser.parse_args()
    matched, unresolved = audit(read(args.canonical), read(args.staged))
    for path, rows in ((args.matched, matched), (args.unresolved, unresolved)):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"exact_matches": len(matched), "unresolved": len(unresolved),
                      "weather_ready": 0, "reason": "stadium_coordinates_not_verified"}))


if __name__ == "__main__":
    main()
