"""Connect dated historical external records to normalized fixtures.

Input JSONL rows must include league_season_file, home_team, away_team,
match_date, source_id, available_at, and factor_group.
Unmatched or temporally unverified rows are quarantined, not trained on.
"""
import json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from analytics.factor_source_registry import GROUPS

ROOT=Path(__file__).resolve().parents[1]
def utc(value):
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (AttributeError,ValueError): return None

def connect():
    index=defaultdict(list)
    for file in (ROOT/"data/normalized_archive").glob("*.json"):
        for row in json.loads(file.read_text(encoding="utf-8"))["matches"]:
            key=(row["league_season_file"],row["date"],row["home_team"].casefold(),row["away_team"].casefold())
            index[key].append(row)
    totals={"source_records":0,"linked":0,"quarantined":0,"missing_files":0}
    for group in GROUPS:
        file=ROOT/"data/external_prematch"/(group+".jsonl")
        if not file.exists():
            totals["missing_files"]+=1
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            totals["source_records"]+=1
            try:
                row=json.loads(line)
                key=(row["league_season_file"],row["match_date"],row["home_team"].casefold(),row["away_team"].casefold())
                matches=index.get(key,[])
                available=utc(row.get("available_at"))
                kickoff=utc(matches[0].get("kickoff_at")) if len(matches)==1 else None
                if len(matches)==1 and row.get("source_id") and available and kickoff and available<kickoff and row.get("factor_group")==group:
                    totals["linked"]+=1
                else: totals["quarantined"]+=1
            except (KeyError,ValueError,TypeError):
                totals["quarantined"]+=1
    return totals

if __name__=="__main__":
    print(json.dumps(connect(),indent=2))
