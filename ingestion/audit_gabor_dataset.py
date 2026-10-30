"""Audit public historical CSV source and safely match fixtures; never leak match-day stats.

Source: xgabora/Club-Football-Match-Data-2000-2025 (upstream Football-Data
and ClubElo attribution/rights need separate review for downstream use).
"""
import csv
import io
import json
import re
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE="https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/data/"
def normalize(value):
    s=unicodedata.normalize("NFKD",value or "")
    return " ".join(re.findall("[a-z0-9]+","".join(c for c in s if not unicodedata.combining(c)).lower()))
def fetch_csv(name):
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"MatchLens historical research"})
    with urllib.request.urlopen(req,timeout=100) as response:
        raw=response.read()
    return csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="replace")))
def run():
    idx=defaultdict(list)
    for path in (ROOT/"data/normalized_archive").glob("*.json"):
        for m in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            idx[(m["date"],normalize(m["home_team"]),normalize(m["away_team"]))].append(m)
    matches=fetch_csv("Matches.csv")
    total=0;linked=[];columns=matches.fieldnames or []
    for row in matches:
        total+=1
        key=(row.get("MatchDate"),normalize(row.get("HomeTeam")),normalize(row.get("AwayTeam")))
        found=idx.get(key,[])
        if len(found)!=1:continue
        match=found[0]
        try:
            if int(float(row["FTHome"]))!=match["home_goals"] or int(float(row["FTAway"]))!=match["away_goals"]:continue
        except (ValueError,TypeError,KeyError):continue
        linked.append({"match_id":match["match_id"],"source_url":BASE+"Matches.csv",
                       "match_date":row["MatchDate"],
                       "prematch_publication_verified":False,
                       "match_day_stats_allowed_as_same_match_features":False,
                       "available_historical_stat_fields":[x for x in
                           ("HomeShots","AwayShots","HomeTarget","AwayTarget",
                            "HomeFouls","AwayFouls","HomeCorners","AwayCorners",
                            "HomeYellow","AwayYellow","HomeRed","AwayRed")
                           if row.get(x) not in (None,"")]})
    elo=fetch_csv("EloRatings.csv")
    elo_rows=sum(1 for _ in elo)
    # Preserve every validated link; the previous 250-row truncation silently lost matches.
    unique={x["match_id"]:x for x in linked}
    report={"source":BASE,"source_matches":total,"source_elo_snapshots":elo_rows,
            "exact_linked":len(unique),"duplicate_link_rows":len(linked)-len(unique),"prematch_verified":0,
            "match_columns":columns,"links":list(unique.values()),
            "notes":"Only exact fixture/date/team/score links. Match-day stats are postmatch and forbidden as same-match predictors. Elo snapshot dates are not publication timestamps; do not claim full factor validation."}
    output=ROOT/"data"/"gabor_source_audit.json"
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("links","match_columns")},indent=2))
if __name__=="__main__":run()
