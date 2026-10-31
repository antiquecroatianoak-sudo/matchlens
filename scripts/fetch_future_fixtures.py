"""Retrieve upcoming fixtures with verified kickoff instants only.

OpenFootball date-only records do not establish an exact kickoff time.
Never fabricate midnight UTC or a live match from a calendar date.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

LEAGUES=("en.1","it.1","es.1","de.1","fr.1","pt.1","be.1","nl.1","tr.1","gr.1")
BASE="https://raw.githubusercontent.com/openfootball/football.json/master"
TZ_RE=re.compile(r"(?:Z|[+-][0-9]{2}:[0-9]{2})$")

def kickoff_instant(match):
    date=match.get("date")
    if not isinstance(date,str):
        return None
    # Date-only and timezone-free times are not verified instants.
    raw=match.get("datetime") or date
    if not isinstance(raw,str) or "T" not in raw or not TZ_RE.search(raw):
        return None
    try:
        dt=datetime.fromisoformat(raw.replace("Z","+00:00"))
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None

def fetch(now=None,days=14):
    now=now or datetime.now(timezone.utc)
    fixtures=[]; errors=[]; date_only=0; seen=set()
    for year in range(now.year-1,now.year+2):
        season=f"{year}-{(year+1)%100:02d}"
        for league in LEAGUES:
            url=f"{BASE}/{season}/{league}.json"
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"MatchLens/1.0"}),timeout=12) as response:
                    data=json.load(response)
            except Exception as exc:
                errors.append({"league":league,"season":season,"error":str(exc)[:100]})
                continue
            for m in data.get("matches",[]):
                if m.get("score") is not None or m.get("ft") is not None:
                    continue
                home=m.get("team1") or m.get("home")
                away=m.get("team2") or m.get("away")
                if not isinstance(home,str) or not isinstance(away,str):
                    continue
                kickoff=kickoff_instant(m)
                if kickoff is None:
                    date_only+=1
                    continue
                if not now<kickoff<=now+timedelta(days=days):
                    continue
                identifier=f"{season}:{league}:{kickoff.isoformat()}:{home}:{away}"
                if identifier in seen:
                    continue
                seen.add(identifier)
                fixtures.append({"id":identifier,"league":league,"season":season,
                    "round":str(m.get("round","unknown")),"kickoff_utc":kickoff.isoformat(),
                    "home":home,"away":away,"source":url})
    from scripts.football_data_fixture_candidates import fetch_candidates
    try:
        candidates=fetch_candidates(now=now,days=days)
    except Exception as exc:
        candidates=[]
        errors.append({"source":"football-data-fixtures","error":str(exc)[:120]})
    return {"fetched_at_utc":now.isoformat(),"fixtures":fixtures,
        "unverified_time_candidates":candidates,
        "source_errors":errors,"skipped_without_verified_kickoff":date_only,
        "probabilities_available":False,
        "status":"fixtures_only_no_predictions_until_prematch_model_feed"}

def main():
    result=fetch()
    out=Path("out/future-fixtures.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("UPCOMING VERIFIED KICKOFFS",len(result["fixtures"]),
        "UNVERIFIED KICKOFFS",result["skipped_without_verified_kickoff"],
        "SOURCE ERRORS",len(result["source_errors"]))
    print("FOOTBALL-DATA UNVERIFIED TIME CANDIDATES",len(result["unverified_time_candidates"]))
    print("NO LIVE SCORE OR BOOKMAKER ODDS: no verified feed connected")

if __name__=="__main__":
    main()
