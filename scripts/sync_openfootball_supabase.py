"""Bulk OpenFootball fixture sync into the separate Supabase fixture staging table.

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY GitHub secrets.
Never writes model training datasets or optional factor observations.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

LEAGUES = ("en.1", "it.1", "es.1", "de.1", "fr.1", "pt.1", "be.1", "nl.1", "tr.1", "gr.1")
BASE = "https://github.com/openfootball/football.json/blob/master"
BATCH_SIZE = 500


def fixture_rows():
    for path in sorted(Path("data/openfootball").glob("*.json")):
        parts = path.name.split(".")
        if len(parts) != 4:
            continue
        season, country, division, extension = parts
        league = f"{country}.{division}"
        if extension != "json" or league not in LEAGUES:
            continue
        try:
            matches = json.loads(path.read_text(encoding="utf-8")).get("matches", [])
        except (ValueError, OSError) as exc:
            print("SKIP malformed file", path, str(exc), flush=True)
            continue
        for match in matches:
            home = match.get("team1") or match.get("home")
            away = match.get("team2") or match.get("away")
            date = str(match.get("date") or "")[:10]
            if not (home and away and len(date) == 10 and date[4] == "-" and date[7] == "-"):
                continue
            identifier = f"openfootball:{league}:{date}:{home}:{away}"
            yield {"id": identifier, "source": "openfootball",
                   "source_url": f"{BASE}/{season}/{league}.json",
                   "match_date": date, "league": league,
                   "home_team": str(home), "away_team": str(away)}


def upload(batch, url, key):
    endpoint = url.rstrip("/") + "/rest/v1/fixtures?on_conflict=id"
    body = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=minimal",
        "User-Agent": "MatchLensBulkImport/1.0",
    })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                if response.status not in (200, 201, 204):
                    raise RuntimeError(f"Unexpected Supabase status {response.status}")
            return
        except urllib.error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace")
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError):
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY; no database write attempted")
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    if host != "jhsakrbcdjabxkgdalta.supabase.co":
        raise SystemExit("Refusing fixture import: SUPABASE_URL is not the isolated MatchLens project")
    total = 0
    batch = []
    seen = set()
    for row in fixture_rows():
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            upload(batch, url, key)
            total += len(batch)
            print("Uploaded fixture batch; processed", total, flush=True)
            batch.clear()
    if batch:
        upload(batch, url, key)
        total += len(batch)
    print("Bulk import complete; rows processed", total, "(duplicates ignored by primary key)", flush=True)


if __name__ == "__main__":
    main()
