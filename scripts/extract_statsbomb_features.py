"""Research-only StatsBomb event feature extraction; no database writes."""
import argparse
import csv
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/hudl/open-data/master/data/events"
FIELDS = ["match_id", "team_id", "team_name", "shots", "xg_sum", "passes", "completed_passes", "pressures", "interceptions", "duels", "source"]

def extract(match_id, events):
    teams = {}
    for e in events:
        team = e.get("team") or {}
        tid = team.get("id")
        if tid is None:
            continue
        if tid not in teams:
            teams[tid] = dict(match_id=match_id, team_id=tid, team_name=team.get("name", ""), shots=0, xg_sum=0.0, passes=0, completed_passes=0, pressures=0, interceptions=0, duels=0, source=f"hudl/open-data/events/{match_id}.json")
        row = teams[tid]
        kind = (e.get("type") or {}).get("name")
        if kind == "Shot":
            row["shots"] += 1
            xg = (e.get("shot") or {}).get("statsbomb_xg")
            if xg is not None:
                value = float(xg)
                if not math.isfinite(value) or value < 0 or value > 1:
                    raise ValueError(f"invalid shot xG in match {match_id}, team {tid}: {xg!r}")
                row["xg_sum"] += value
        elif kind == "Pass":
            row["passes"] += 1
            if not (e.get("pass") or {}).get("outcome"):
                row["completed_passes"] += 1
        elif kind == "Pressure":
            row["pressures"] += 1
        elif kind == "Interception":
            row["interceptions"] += 1
        elif kind == "Duel":
            row["duels"] += 1
    return list(teams.values())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--matches", required=True, help="Local matches.json from the pilot importer")
    p.add_argument("--output", default="data/statsbomb_pilot/team_features.csv")
    p.add_argument("--max-matches", type=int, default=0, help="0 = all")
    args = p.parse_args()
    matches = json.loads(Path(args.matches).read_text(encoding="utf-8"))
    if args.max_matches < 0:
        p.error("--max-matches must be nonnegative")
    rows = []
    failures = []
    for match in matches[:args.max_matches or None]:
        mid = match["match_id"]
        try:
            req = Request(f"{BASE}/{mid}.json", headers={"User-Agent": "MatchLens-research-pilot/0.1"})
            with urlopen(req, timeout=30) as res:
                events = json.load(res)
            rows.extend(extract(mid, events))
        except Exception as exc:
            failures.append({"match_id": mid, "error": str(exc)})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = {"matches_requested": len(matches[:args.max_matches or None]), "team_rows": len(rows), "failed": failures, "production_import": False, "note": "Full-match postgame features; NEVER use as prematch features for the same match."}
    output.with_suffix(".report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
