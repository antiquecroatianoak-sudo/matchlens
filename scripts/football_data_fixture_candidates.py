"""Read Football-Data's published fixture CSV without fabricating UTC kickoff times.

The provider's CSV contains local clock times but no timezone offset. Keep these
as unverified local times until the source's timezone convention is established.
"""
import csv
import io
import urllib.request
from datetime import datetime, timezone, timedelta

URL = "https://www.football-data.co.uk/fixtures.csv"

def fetch_candidates(now=None, days=14):
    now = now or datetime.now(timezone.utc)
    with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "MatchLens/1.0"}), timeout=20) as response:
        raw = response.read(3_000_000)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))
    if not {"Date", "Time", "HomeTeam", "AwayTeam"}.issubset(set(reader.fieldnames or [])):
        raise ValueError("Fixture CSV missing required date/time/team columns")
    candidates = []
    seen = set()
    for row in reader:
        try:
            date_text = (row.get("Date") or "").strip()
            day = None
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d/%m/%Y %H:%M"):
                try:
                    day = datetime.strptime(date_text, fmt).date()
                    break
                except ValueError:
                    pass
            if day is None or not now.date() <= day <= (now + timedelta(days=days)).date():
                continue
            clock = (row.get("Time") or "").strip()
            datetime.strptime(clock, "%H:%M")
            home = (row.get("HomeTeam") or "").strip()
            away = (row.get("AwayTeam") or "").strip()
            if not home or not away:
                continue
            key = (row.get("Div"), date_text, clock, home, away)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"league": (row.get("Div") or "").strip(), "date": day.isoformat(),
                               "local_time_unverified": clock, "home": home, "away": away,
                               "source": URL, "kickoff_utc": None, "kickoff_verified": False})
        except (ValueError, TypeError):
            continue
    return candidates
