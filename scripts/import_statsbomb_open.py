"""StatsBomb Open Data pilot: explicit local import, no production writes.

Usage: python scripts/import_statsbomb_open.py --output-dir data/statsbomb_pilot
Fetches competition catalogue and one selected season. Research-only data;
verify the provider agreement before commercial use or publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/hudl/open-data/master/data"

def fetch(path):
    request = Request(f"{BASE}/{path}", headers={"User-Agent": "MatchLens-research-pilot/0.1"})
    with urlopen(request, timeout=30) as response:
        payload = response.read()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition-id", type=int, default=9)
    parser.add_argument("--season-id", type=int, default=281)
    parser.add_argument("--output-dir", default="data/statsbomb_pilot")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    competitions, catalogue_hash = fetch("competitions.json")
    eligible = [c for c in competitions if c["competition_id"] == args.competition_id and c["season_id"] == args.season_id]
    if not eligible:
        raise SystemExit("Competition/season not in provider catalogue; nothing imported")
    matches, matches_hash = fetch(f"matches/{args.competition_id}/{args.season_id}.json")
    if not isinstance(matches, list):
        raise ValueError("Invalid match payload")
    ids = [m["match_id"] for m in matches]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate match IDs in source")
    (out / "matches.json").write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"provider": "Hudl StatsBomb Open Data", "scope": "research_only", "competition_id": args.competition_id, "season_id": args.season_id, "match_count": len(matches), "catalogue_sha256": catalogue_hash, "matches_sha256": matches_hash, "source": f"{BASE}/matches/{args.competition_id}/{args.season_id}.json", "production_import": False}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
