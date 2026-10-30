"""Prepare verified kickoff/venue manifests for grouped weather imports.

Never infer a kickoff time from a date-only fixture. Never assume a team's
home stadium when neutral grounds or venue changes are possible.
Two inputs are joined on the canonical fixture ID, not on team names.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

START, END = "2024-10-30", "2026-10-30"


def load(path):
    result = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = row["id"]
        if key in result:
            raise ValueError("Duplicate fixture id: " + key)
        result[key] = row
    return result


def build(fixtures, metadata):
    ready, issues = [], []
    for key, row in fixtures.items():
        day = str(row.get("date", ""))[:10]
        if not START <= day <= END:
            continue
        m = metadata.get(key)
        if not m:
            issues.append({"id": key, "reason": "missing_verified_metadata"})
            continue
        try:
            stamp = datetime.fromisoformat(m["kickoff_utc"].replace("Z", "+00:00"))
            if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
                raise ValueError("kickoff_not_utc")
            if stamp.date().isoformat() != day:
                # Date-only league feeds may use a local date, so flag for review.
                raise ValueError("kickoff_date_mismatch")
            if not m.get("source_url") or not m.get("verified_venue"):
                raise ValueError("missing_provenance_or_venue_verification")
            lat, lon = float(m["latitude"]), float(m["longitude"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("invalid_coordinates")
            ready.append({"id": key, "kickoff_utc": m["kickoff_utc"],
                          "latitude": lat, "longitude": lon,
                          "source_url": m["source_url"], "verified_venue": m["verified_venue"]})
        except (KeyError, TypeError, ValueError) as error:
            issues.append({"id": key, "reason": str(error)})
    return ready, issues


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", required=True, help="Canonical fixture JSONL")
    p.add_argument("--metadata", required=True, help="Verified kickoff/venue JSONL")
    p.add_argument("--output", required=True)
    p.add_argument("--issues", required=True)
    a = p.parse_args()
    ready, issues = build(load(a.fixtures), load(a.metadata))
    for name, rows in ((a.output, ready), (a.issues, issues)):
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"ready": len(ready), "missing_or_invalid": len(issues)}))


if __name__ == "__main__":
    main()
