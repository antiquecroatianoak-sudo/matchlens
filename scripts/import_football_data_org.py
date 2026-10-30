"""Fetch football-data.org fixture metadata in season-level batches.

Only stages kickoff and team IDs. This API does not guarantee a verified
physical stadium; weather ingestion must still pass venue verification.
Requires FOOTBALL_DATA_ORG_TOKEN, never commits credentials.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

COMPETITIONS = ("PL", "PD", "SA", "BL1", "FL1", "DED", "PPL", "BSA")
BASE = "https://api.football-data.org/v4/competitions/"


def fetch(code, season, token):
    url = BASE + code + "/matches?" + urlencode({"season": season})
    request = Request(url, headers={"X-Auth-Token": token})
    try:
        with urlopen(request, timeout=40) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"{code}/{season}: HTTP {exc.code} (plan, quota or coverage)") from exc
    return payload.get("matches", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026])
    parser.add_argument("--competitions", nargs="+", default=list(COMPETITIONS))
    args = parser.parse_args()
    token = os.environ.get("FOOTBALL_DATA_ORG_TOKEN")
    if not token:
        parser.error("FOOTBALL_DATA_ORG_TOKEN missing: import not run")
    staged, report = [], []
    for code in args.competitions:
        for season in args.seasons:
            try:
                matches = fetch(code, season, token)
                for match in matches:
                    kickoff = match.get("utcDate")
                    if not kickoff or not ("2024-10-30" <= kickoff[:10] <= "2026-10-30"):
                        continue
                    staged.append({
                        "provider": "football-data.org", "provider_id": match.get("id"),
                        "competition": code, "season": season, "kickoff_utc": kickoff,
                        "home": (match.get("homeTeam") or {}).get("name"),
                        "away": (match.get("awayTeam") or {}).get("name"),
                        "home_team_id": (match.get("homeTeam") or {}).get("id"),
                        "away_team_id": (match.get("awayTeam") or {}).get("id"),
                        "status": match.get("status"),
                        "source_url": "https://api.football-data.org/v4/matches/" + str(match.get("id")),
                        "verified_venue": None,
                    })
                report.append({"competition": code, "season": season, "status": "ok", "matches": len(matches)})
            except (RuntimeError, OSError, ValueError) as error:
                report.append({"competition": code, "season": season, "status": "failed", "error": str(error)})
    for filename, rows in ((args.output, staged), (args.report, report)):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"staged": len(staged), "successful_batches": sum(x["status"] == "ok" for x in report),
                      "failed_batches": sum(x["status"] == "failed" for x in report)}))


if __name__ == "__main__":
    main()
