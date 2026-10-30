"""Download actual StatsBomb match metadata; preserve provenance and uncertainty.

No match-day metadata is asserted to have been published before kickoff.
"""
import json
import urllib.request
from pathlib import Path
from datetime import datetime,timezone

BASE="https://raw.githubusercontent.com/hudl/open-data/master/data/"
ROOT=Path(__file__).resolve().parents[1]
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"MatchLens-research/1.0"})
    with urllib.request.urlopen(req,timeout=35) as response:
        return json.load(response)
def run(max_seasons=12):
    catalog=fetch(BASE+"competitions.json")
    catalog=sorted(catalog,key=lambda c:(str(c.get("season_name","")),str(c.get("competition_name",""))),reverse=True)
    results=[]
    failures=[]
    for comp in catalog[:max_seasons]:
        cid,sid=comp["competition_id"],comp["season_id"]
        url=BASE+f"matches/{cid}/{sid}.json"
        try:
            matches=fetch(url)
            for match in matches:
                results.append({
                    "external_match_id":match.get("match_id"),
                    "match_date":match.get("match_date"),
                    "kick_off_source_value":match.get("kick_off"),
                    "competition":comp.get("competition_name"),
                    "season":comp.get("season_name"),
                    "home_team":match.get("home_team",{}).get("home_team_name"),
                    "away_team":match.get("away_team",{}).get("away_team_name"),
                    "stadium":(match.get("stadium") or {}).get("name"),
                    "referee":(match.get("referee") or {}).get("name"),
                    "home_manager":(match.get("home_team",{}).get("managers") or [{}])[0].get("name"),
                    "away_manager":(match.get("away_team",{}).get("managers") or [{}])[0].get("name"),
                    "source_url":url,
                    "source_last_updated":match.get("last_updated"),
                    "prematch_publication_verified":False})
        except Exception as exc:
            failures.append({"url":url,"error":str(exc)})
    out=ROOT/"data"/"statsbomb_external_matches.json"
    out.write_text(json.dumps({"retrieved_at":datetime.now(timezone.utc).isoformat(),
        "notice":"Post-match metadata; NOT certified prematch availability.",
        "records":results,"failures":failures},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"downloaded_matches":len(results),"season_files_requested":max_seasons,
        "failures":len(failures),"prematch_verified":0},indent=2))
if __name__=="__main__":run()
