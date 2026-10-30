"""Match external fixture metadata by exact dates and conservative team-name normalization.

A match link does not imply its metadata was published before kickoff.
"""
import json
import re
import unicodedata
from difflib import SequenceMatcher
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
    by_day=defaultdict(list)
    for (day,_,_),matches in index.items():
        by_day[day].extend(matches)
    linked=[]
    ambiguous=0
    fuzzy_linked=0
    for row in external:
        key=(row.get("match_date"),norm(row.get("home_team")),norm(row.get("away_team")))
        matches=index.get(key,[])
        used_fuzzy=False
        if not matches and row.get('home_goals') is not None and row.get('away_goals') is not None:
            pool=[m for m in by_day.get(row.get('match_date'),[]) if m['home_goals']==row['home_goals'] and m['away_goals']==row['away_goals']]
            scored=sorted(((min(SequenceMatcher(None,norm(row['home_team']),norm(m['home_team'])).ratio(),SequenceMatcher(None,norm(row['away_team']),norm(m['away_team'])).ratio()),m) for m in pool),key=lambda x:x[0],reverse=True)
            if scored and scored[0][0]>=0.82 and (len(scored)==1 or scored[0][0]-scored[1][0]>=0.12):
                matches=[scored[0][1]]
                used_fuzzy=True
        if len(matches)==1:
            if used_fuzzy: fuzzy_linked+=1
            linked.append({"match_id":matches[0]["match_id"],
                "match_method":"fuzzy_teams_date_score" if used_fuzzy else "exact_teams_date",
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
        "ambiguous":ambiguous,"fuzzy_linked":fuzzy_linked,"prematch_verified":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"external_count":len(external),"linked":len(linked),
                      "ambiguous":ambiguous,"prematch_verified":0},indent=2))
if __name__=="__main__":link()
