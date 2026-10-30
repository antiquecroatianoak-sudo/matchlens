"""Fetch public StatsBomb match metadata in competition/season batches.

Only publicly released matches are imported. Missing stadiums remain missing.
No API key required. Usage subject to StatsBomb open-data terms.
"""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

BASE="https://raw.githubusercontent.com/statsbomb/open-data/master/data/"

def get_json(path):
    with urlopen(BASE+path, timeout=35) as response:
        return json.load(response)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    competitions=get_json("competitions.json")
    rows=[]; report=[]
    for comp in competitions:
        cid=comp["competition_id"]; sid=comp["season_id"]
        try:
            matches=get_json(f"matches/{cid}/{sid}.json")
        except (OSError,ValueError) as exc:
            report.append({"competition_id":cid,"season_id":sid,"status":"failed","reason":str(exc)})
            continue
        kept=0
        for m in matches:
            date=m.get("match_date","")
            if not ("2024-10-30" <= date <= "2026-10-30"):
                continue
            venue=m.get("stadium") or {}
            rows.append({"provider":"statsbomb-open-data","provider_id":m.get("match_id"),
                "date":date,"kickoff_local":m.get("kick_off"),
                "competition":comp.get("competition_name"),
                "season":comp.get("season_name"),
                "home":(m.get("home_team") or {}).get("home_team_name"),
                "away":(m.get("away_team") or {}).get("away_team_name"),
                "stadium_id":venue.get("id"),"venue_name":venue.get("name"),
                "country":(venue.get("country") or {}).get("name"),
                "source_url":BASE+f"matches/{cid}/{sid}.json",
                "kickoff_utc":None,"venue_latitude":None,"venue_longitude":None})
            kept+=1
        report.append({"competition_id":cid,"season_id":sid,"status":"ok","matches_in_window":kept})
    for name,data in ((a.output,rows),(a.report,report)):
        path=Path(name);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in data),encoding="utf-8")
    print(json.dumps({"matches_in_window":len(rows),"batches":len(report),
                      "with_stadium":sum(bool(r["venue_name"]) for r in rows),
                      "weather_ready":0,
                      "note":"UTC kickoff and verified venue coordinates still required"}))

if __name__=="__main__":
    main()
