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
from datetime import datetime, timezone
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True, help="Verified venue and kickoff JSONL")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    with output.open("w", encoding="utf-8") as out:
        for line in Path(args.fixtures).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                result = fetch(row)
            except (KeyError, ValueError, OSError) as error:
                skipped += 1
                print(json.dumps({"id": row.get("id"), "skipped": str(error)}), flush=True)
                continue
            out.write(json.dumps(result) + "\n")
            ok += 1
    print(json.dumps({"weather_rows": ok, "skipped": skipped, "output": str(output)}))


if __name__ == "__main__":
    main()
