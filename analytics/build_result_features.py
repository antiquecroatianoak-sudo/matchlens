"""Leakage-safe historical features derived from dated match results.

Features are available only from games at least two calendar days earlier.
These are historical result features, not independent pre-match source snapshots.
"""
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build():
    rows=[]
    for path in sorted((ROOT/"data/normalized_archive").glob("*.json")):
        for match in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            rows.append(match)
    rows.sort(key=lambda r:(r["date"],r["match_id"]))
    history=defaultdict(list)
    output=[]
    for match in rows:
        day=date.fromisoformat(match["date"])
        def features(team):
            prior=[r for r in history[team] if date.fromisoformat(r["date"]) <= day-timedelta(days=2)]
            last=prior[-15:]
            if not last: return None
            goals_for=[r["home_goals"] if r["home_team"]==team else r["away_goals"] for r in last]
            goals_against=[r["away_goals"] if r["home_team"]==team else r["home_goals"] for r in last]
            points=sum(3 if f>a else 1 if f==a else 0 for f,a in zip(goals_for,goals_against))
            days_since=(day-date.fromisoformat(last[-1]["date"])).days
            return {"matches":len(last),"goals_for_per_match":sum(goals_for)/len(last),
                    "goals_against_per_match":sum(goals_against)/len(last),
                    "points_per_match":points/len(last),"rest_days_lower_bound":days_since}
        home=features(match["home_team"])
        away=features(match["away_team"])
        if home and away:
            output.append({"match_id":match["match_id"],"match_date":match["date"],
                           "source_id":"normalized_openfootball_prior_results",
                           "feature_cutoff_date":(day-timedelta(days=2)).isoformat(),
                           "home":home,"away":away,
                           "available_at":None,
                           "timestamp_verified":False})
        history[match["home_team"]].append(match)
        history[match["away_team"]].append(match)
    return output

if __name__=="__main__":
    rows=build()
    print(json.dumps({"total_with_history":len(rows),"timestamp_verified":0,
                      "example":rows[0] if rows else None},indent=2))
