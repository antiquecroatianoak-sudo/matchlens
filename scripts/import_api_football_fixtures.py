"""Batch import API-Football historical fixture kickoff and venue metadata.

Requires API_FOOTBALL_KEY environment variable and season/league access.
This adapter never guesses venue coordinates; output is a staging file that
must be enriched with verified venue coordinates before weather import.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LEAGUES = {"en.1":39, "it.1":135, "es.1":140, "de.1":78, "fr.1":61,
           "pt.1":94, "be.1":144, "nl.1":88, "tr.1":203, "gr.1":197}
ENDPOINT = "https://v3.football.api-sports.io/fixtures"


def fetch(league, season, key):
    url = ENDPOINT + "?" + urlencode({"league": LEAGUES[league], "season": season})
    request = Request(url, headers={"x-apisports-key": key})
    with urlopen(request, timeout=40) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    return payload.get("response", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026])
    parser.add_argument("--leagues", nargs="+", choices=sorted(LEAGUES), default=sorted(LEAGUES))
    args = parser.parse_args()
    key = os.getenv("API_FOOTBALL_KEY")
    if not key:
        parser.error("API_FOOTBALL_KEY is required; no fixture data imported")
    rows = []
    for league in args.leagues:
        for season in args.seasons:
            fixtures = fetch(league, season, key)
            for entry in fixtures:
                fixture = entry.get("fixture") or {}
                venue = fixture.get("venue") or {}
                teams = entry.get("teams") or {}
                rows.append({"provider": "api-football", "provider_id": fixture.get("id"),
                             "league": league, "season": season, "kickoff_utc": fixture.get("date"),
                             "home": (teams.get("home") or {}).get("name"),
                             "away": (teams.get("away") or {}).get("name"),
                             "venue_id": venue.get("id"), "venue_name": venue.get("name"),
                             "venue_city": venue.get("city"),
                             "source_url": "https://v3.football.api-sports.io/fixtures?id=" + str(fixture.get("id"))})
            print(json.dumps({"league": league, "season": season, "received": len(fixtures)}), flush=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"staged_fixtures": len(rows), "output": str(output)}))


if __name__ == "__main__":
    main()
