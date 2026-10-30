"""Canonical provenance manifest for all pre-match factor families.

Only observed, timestamped sources may enter the full-factor model.
A missing source is missing data, never a zero-valued observation.
"""
import json
from pathlib import Path

GROUPS={
 "attack_defense":"prior completed match goals",
 "home_away":"prior home and away completed matches",
 "elo":"sequential rating from prior results",
 "form":"prior results and points",
 "rest_travel":"previous match dates; travel requires verified venue coordinates",
 "coach":"historical coach appointment and departure timestamps",
 "player_matchups":"historical player availability and positions",
 "lineups":"historical published lineup snapshots",
 "injuries_suspensions":"historical injury and suspension announcements",
 "tactics":"historical pre-kickoff formation snapshots",
 "weather":"archived forecasts published before kickoff, not observed weather",
 "pitch":"historical pre-kickoff pitch condition reports",
 "motivation":"historical pre-kickoff standings and competition stakes",
 "referee":"historical referee assignments announced before kickoff"
}
ROOT=Path(__file__).resolve().parents[1]
def report():
    result={}
    for name,description in GROUPS.items():
        path=ROOT/"data/historical_factors"/(name+".jsonl")
        result[name]={"description":description,"source_file_exists":path.exists(),
                      "status":"requires verified historical source and availability timestamp"}
    return result
if __name__=="__main__":
    print(json.dumps(report(),indent=2,ensure_ascii=False))
