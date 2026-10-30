"""Import external StatsBomb match metadata with strict match identity checks.

This is source discovery, not prematch lineup availability proof.
The open-data repository does not establish original publication times.
"""
import json
import urllib.request
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
BASE="https://raw.githubusercontent.com/statsbomb/open-data/master/data/"
def get(path):
    with urllib.request.urlopen(BASE+path,timeout=25) as response:
        return json.load(response)
def run():
    competitions=get("competitions.json")
    catalog=[]
    for item in competitions:
        catalog.append({"competition_id":item["competition_id"],"season_id":item["season_id"],
                        "competition_name":item.get("competition_name"),
                        "country_name":item.get("country_name"),
                        "season_name":item.get("season_name"),
                        "match_updated":item.get("match_updated"),
                        "match_available":item.get("match_available"),
                        "source_url":BASE+"matches/%s/%s.json"%(item["competition_id"],item["season_id"]),
                        "original_prematch_publication_verified":False})
    output=ROOT/"data"/"external_source_catalog_statsbomb.json"
    output.write_text(json.dumps({"source":"StatsBomb Open Data",
       "notice":"Match updated/available fields do not prove a lineup was published before kickoff.",
       "competition_seasons":catalog},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"competition_seasons":len(catalog),"output":str(output),
            "verified_prematch_observations":0}
if __name__=="__main__":
    print(json.dumps(run(),indent=2))
