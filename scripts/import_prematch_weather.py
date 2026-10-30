"""Import pre-match weather forecasts only for fixtures with verified UTC kickoff and venue coordinates.

Input JSONL: {"id": "...", "kickoff_utc": "2025-01-01T18:00:00Z",
              "latitude": 51.5, "longitude": -0.1}
Uses Open-Meteo Previous Runs API: *_previous_day1 means forecast issued 24h
before the valid hour, not a retrospective observation. Missing data stay missing.
No weather field is silently imputed and no outcome is used.
"""
import argparse
import json
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

FIELDS = ("temperature_2m", "precipitation", "wind_speed_10m", "relative_humidity_2m")
BASE = "https://previous-runs-api.open-meteo.com/v1/forecast"


def fetch(row):
    when = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
    if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
        raise ValueError("kickoff_utc must have UTC timezone")
    lat, lon = float(row["latitude"]), float(row["longitude"])
    if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid venue coordinates")
    params = dict(latitude=lat, longitude=lon, start_date=when.date().isoformat(),
                  end_date=when.date().isoformat(), timezone="GMT",
                  hourly=",".join(f + "_previous_day1" for f in FIELDS))
    with urlopen(BASE + "?" + urlencode(params), timeout=30) as response:
        data = json.load(response)
    hourly = data.get("hourly") or {}
    target = when.strftime("%Y-%m-%dT%H:00")
    if target not in hourly.get("time", []):
        raise ValueError("Forecast hour not available")
    idx = hourly["time"].index(target)
    weather = {}
    for field in FIELDS:
        values = hourly.get(field + "_previous_day1") or []
        value = values[idx] if idx < len(values) else None
        weather[field] = float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None
    return {"id": row["id"], "kickoff_utc": row["kickoff_utc"], "weather": weather,
            "source": "Open-Meteo Previous Runs, 24h lead", "venue_latitude": lat,
            "venue_longitude": lon}


def fetch_group(rows):
    """One API call per venue/day, even if several fixtures share that group."""
    first = rows[0]
    when = datetime.fromisoformat(first["kickoff_utc"].replace("Z", "+00:00"))
    lat, lon = float(first["latitude"]), float(first["longitude"])
    params = dict(latitude=lat, longitude=lon, start_date=when.date().isoformat(),
                  end_date=when.date().isoformat(), timezone="GMT",
                  hourly=",".join(f + "_previous_day1" for f in FIELDS))
    with urlopen(BASE + "?" + urlencode(params), timeout=30) as response:
        hourly = (json.load(response).get("hourly") or {})
    times = hourly.get("time", [])
    output = []
    for row in rows:
        target = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00")).strftime("%Y-%m-%dT%H:00")
        if target not in times:
            raise ValueError("Forecast hour not available")
        idx = times.index(target)
        weather = {}
        for field in FIELDS:
            values = hourly.get(field + "_previous_day1") or []
            value = values[idx] if idx < len(values) else None
            weather[field] = float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None
        output.append(dict(id=row["id"], kickoff_utc=row["kickoff_utc"], weather=weather,
                           source="Open-Meteo Previous Runs, 24h lead",
                           venue_latitude=lat, venue_longitude=lon))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True, help="Verified venue and kickoff JSONL")
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    output = Path(args.output)
    if args.workers < 1 or args.workers > 8:
        parser.error("--workers must be between 1 and 8")
    output.parent.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    skipped = 0
    for line in Path(args.fixtures).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        try:
            when = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
                raise ValueError("UTC kickoff required")
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Invalid coordinates")
            if not ("2024-10-30" <= when.date().isoformat() <= "2026-10-30"):
                raise ValueError("Outside two-year research window")
            groups[(lat, lon, when.date().isoformat())].append(row)
        except (KeyError, ValueError) as error:
            skipped += 1
            print(json.dumps({"id": row.get("id"), "skipped": str(error)}), flush=True)
    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool, output.open("w", encoding="utf-8") as out:
        futures = {pool.submit(fetch_group, group): group for group in groups.values()}
        for future in as_completed(futures):
            try:
                results = future.result()
            except (ValueError, OSError) as error:
                skipped += len(futures[future])
                print(json.dumps({"group_skipped": len(futures[future]), "reason": str(error)}), flush=True)
                continue
            for result in results:
                out.write(json.dumps(result) + "\n")
                ok += 1
    print(json.dumps({"weather_rows": ok, "skipped": skipped, "api_groups": len(groups), "output": str(output)}))


if __name__ == "__main__":
    main()
