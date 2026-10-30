"""Audit real, timestamped pre-match factor records without inventing values."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = (
    "attack_defense", "home_away", "elo", "form", "rest_travel",
    "coach", "player_matchups", "lineups", "injuries_suspensions",
    "tactics", "weather", "pitch", "motivation", "referee",
)

def run():
    archive = ROOT / "data/normalized_archive"
    factor_root = ROOT / "data/historical_factors"
    files = sorted(archive.glob("*.json"))
    counts = Counter()
    matches = set()
    for file in files:
        for row in json.loads(file.read_text(encoding="utf-8"))["matches"]:
            matches.add(row["match_id"])
            counts[file.name.split("-")[-1].removesuffix(".json")] += 1
    factors = {}
    for group in GROUPS:
        path = factor_root / (group + ".jsonl")
        present = 0
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("match_id") in matches and row.get("source_id") and row.get("available_at"):
                    present += 1
        factors[group] = {"file_exists": path.exists(), "records_with_source_and_timestamp": present}
    return {"source_files": len(files), "matches": len(matches),
            "league_codes": sorted(counts), "factor_inventory": factors,
            "full_factor_test_ready": False,
            "reason": "Factor timestamps must be independently checked against verified kickoff instants."}

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
