"""Normalize archived OpenFootball match results without fabricating kickoff times."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/upstream_openfootball"
DEST = ROOT / "data/normalized_archive"

def run():
    DEST.mkdir(parents=True, exist_ok=True)
    report = {"source_files": 0, "matches": 0, "rejected": [], "by_file": {}}
    seen = set()
    for path in sorted(SOURCE.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data["matches"]
            if not isinstance(rows, list):
                raise ValueError("matches is not a list")
            normalized = []
            for row in rows:
                score = row.get("score") or {}
                ft = score.get("ft") if isinstance(score, dict) else None
                if not isinstance(ft, list) or len(ft) != 2 or not all(isinstance(v, int) and v >= 0 for v in ft):
                    continue
                day, home, away = row.get("date"), row.get("team1"), row.get("team2")
                if not all(isinstance(v, str) and v for v in (day, home, away)):
                    raise ValueError("missing date or team")
                identity = (path.name, day, home, away)
                if identity in seen:
                    raise ValueError("duplicate match")
                seen.add(identity)
                match_id = hashlib.sha256("|".join(identity).encode()).hexdigest()[:24]
                normalized.append({"match_id": match_id, "league_season_file": path.name,
                                   "date": day, "home_team": home, "away_team": away,
                                   "home_goals": ft[0], "away_goals": ft[1],
                                   "kickoff_time_unverified": row.get("time"),
                                   "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            (DEST / path.name).write_text(json.dumps({"source": path.name, "matches": normalized},
                                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report["source_files"] += 1
            report["matches"] += len(normalized)
            report["by_file"][path.name] = len(normalized)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report["rejected"].append({"file": path.name, "reason": str(exc)})
    return report

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
