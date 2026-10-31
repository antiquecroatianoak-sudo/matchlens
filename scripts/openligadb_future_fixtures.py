"""Fetch future fixtures with explicitly provided UTC kickoffs from OpenLigaDB.

OpenLigaDB publishes matchDateTimeUTC separately from its local time.
Do not infer UTC from matchDateTime. All matches remain research candidates
until downstream historical coverage and validation are checked.
"""
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BASE="https://api.openligadb.de/getmatchdata"
LEAGUES=("bl1","bl2")

def fetch_verified(now=None, days=14, leagues=LEAGUES):
    now=now or datetime.now(timezone.utc)
    fixtures=[]; errors=[]; seen=set()
    for league in leagues:
        for season in (now.year-1,now.year):
            url=f"{BASE}/{league}/{season}"
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"MatchLens/1.0"})
                with urllib.request.urlopen(req,timeout=15) as response:
                    matches=json.load(response)
                if not isinstance(matches,list):
                    raise ValueError("Expected list of matches")
            except Exception as exc:
                errors.append({"source":url,"error":str(exc)[:120]})
                continue
            for m in matches:
                if m.get("matchIsFinished") is not False:
                    continue
                raw=m.get("matchDateTimeUTC")
                if not isinstance(raw,str) or not raw.strip():
                    continue
                try:
                    kickoff=datetime.fromisoformat(raw.replace("Z","+00:00"))
                    if kickoff.tzinfo is None:
                        # Provider field is explicitly defined as UTC.
                        kickoff=kickoff.replace(tzinfo=timezone.utc)
                    kickoff=kickoff.astimezone(timezone.utc)
                except ValueError:
                    continue
                if not now<kickoff<=now+timedelta(days=days):
                    continue
                home=(m.get("team1") or {}).get("teamName")
                away=(m.get("team2") or {}).get("teamName")
                mid=m.get("matchID")
                if not home or not away or not isinstance(mid,int):
                    continue
                identifier=f"openligadb:{mid}"
                if identifier in seen:
                    continue
                seen.add(identifier)
                fixtures.append({"id":identifier,"league":league,"season":str(season),
                    "round":str((m.get("group") or {}).get("groupOrderID","unknown")),
                    "kickoff_utc":kickoff.isoformat(),"home":home,"away":away,
                    "source":url,"source_match_id":mid,"kickoff_source_field":"matchDateTimeUTC"})
    return fixtures,errors
