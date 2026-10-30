"""Match external fixture metadata by exact dates and conservative team-name normalization.

A match link does not imply its metadata was published before kickoff.
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from ingestion.import_statsbomb_matches import run as download

ROOT=Path(__file__).resolve().parents[1]
def norm(value):
    value=unicodedata.normalize("NFKD",value or "")
    value="".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+",value.lower()))
def link():
    download()
    external=json.loads((ROOT/"data/statsbomb_external_matches.json").read_text(encoding="utf-8"))["records"]
    index=defaultdict(list)
    for file in (ROOT/"data/normalized_archive").glob("*.json"):
        for row in json.loads(file.read_text(encoding="utf-8"))["matches"]:
            index[(row["date"],norm(row["home_team"]),norm(row["away_team"]))].append(row)
    linked=[]
    ambiguous=0
    for row in external:
        key=(row.get("match_date"),norm(row.get("home_team")),norm(row.get("away_team")))
        matches=index.get(key,[])
        if len(matches)==1:
            linked.append({"match_id":matches[0]["match_id"],
                "external_match_id":row["external_match_id"],
                "source_url":row["source_url"],
                "kick_off_source_value":row.get("kick_off_source_value"),
                "stadium":row.get("stadium"),"referee":row.get("referee"),
                "home_manager":row.get("home_manager"),
                "away_manager":row.get("away_manager"),
                "prematch_publication_verified":False})
        elif len(matches)>1: ambiguous+=1
    output=ROOT/"data/statsbomb_linked_matches.json"
    output.write_text(json.dumps({"linked":linked,"external_count":len(external),
        "ambiguous":ambiguous,"prematch_verified":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"external_count":len(external),"linked":len(linked),
                      "ambiguous":ambiguous,"prematch_verified":0},indent=2))
if __name__=="__main__":link()
