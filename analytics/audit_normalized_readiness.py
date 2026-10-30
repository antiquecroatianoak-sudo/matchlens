"""Audit the actual normalized archive and prevent date-only kickoff leakage."""
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("attack_defense","home_away","elo","form","rest_travel","coach",
          "player_matchups","lineups","injuries_suspensions","tactics",
          "weather","pitch","motivation","referee")

def utc(value):
    try:
        d = datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,AttributeError):
        return None

def audit():
    files = sorted((ROOT/"data/normalized_archive").glob("*.json"))
    matches = {}
    leagues = Counter()
    duplicate = 0
    for path in files:
        for row in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            mid=row["match_id"]
            duplicate += int(mid in matches)
            matches[mid]=row
            leagues[path.name.split("-")[-1].removesuffix(".json")]+=1
    verified_kickoff = {mid:utc(row.get("kickoff_at")) for mid,row in matches.items()}
    coverage = {}
    for group in GROUPS:
        path=ROOT/"data/historical_factors"/(group+".jsonl")
        good=set()
        rejected=0
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                try: row=json.loads(line)
                except ValueError:
                    rejected+=1
                    continue
                mid=row.get("match_id")
                available=utc(row.get("available_at"))
                kickoff=verified_kickoff.get(mid)
                if mid in matches and row.get("source_id") and available and kickoff and available < kickoff:
                    good.add(mid)
                else: rejected+=1
        coverage[group]={"verified_matches":len(good),"rejected_records":rejected}
    return {"source_files":len(files),"matches":len(matches),
            "leagues":dict(sorted(leagues.items())),
            "duplicate_ids":duplicate,
            "verified_kickoffs":sum(v is not None for v in verified_kickoff.values()),
            "missing_kickoffs":sum(v is None for v in verified_kickoff.values()),
            "factor_coverage":coverage,
            "ready_for_full_backtest":bool(matches) and duplicate==0 and
               all(verified_kickoff.values()) and all(v["verified_matches"]==len(matches)
               for v in coverage.values()),
            "note":"Unknown kickoff time is never inferred from the match date."}

if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
