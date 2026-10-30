"""Import genuine historical StatsBomb events for uniquely linked fixtures.

Event metrics describe completed games, not pre-game information for that same game.
Never use these values to predict their own fixture. A separate pipeline must
lag observations until after the source match and verify publication provenance.
"""
import json
import urllib.request
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE="https://raw.githubusercontent.com/hudl/open-data/master/data/events/"
def download(match_id):
    req=urllib.request.Request(BASE+str(match_id)+".json",headers={"User-Agent":"MatchLens-research/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:
        return json.load(response)
def run(limit=120):
    links=json.loads((ROOT/"data/statsbomb_linked_matches.json").read_text(encoding="utf-8"))["linked"]
    # Deduplicate external match IDs; never guess ambiguous links.
    links=list({str(x["external_match_id"]):x for x in links}.values())[:limit]
    rows=[];errors=[]
    for item in links:
        try:
            events=download(item["external_match_id"])
            stats=defaultdict(Counter)
            for event in events:
                team=(event.get("team") or {}).get("name")
                kind=(event.get("type") or {}).get("name")
                if not team or not kind:continue
                if kind=="Shot":
                    stats[team]["shots"]+=1
                    stats[team]["xg"]+=float((event.get("shot") or {}).get("statsbomb_xg") or 0)
                elif kind=="Foul Committed":stats[team]["fouls_committed"]+=1
                elif kind=="Foul Won":stats[team]["fouls_won"]+=1
                elif kind=="Duel":stats[team]["duels"]+=1
                elif kind=="Pass":stats[team]["passes"]+=1
                elif kind=="Interception":stats[team]["interceptions"]+=1
            rows.append({"match_id":item["match_id"],"external_match_id":item["external_match_id"],
                "source_url":BASE+str(item["external_match_id"])+".json",
                "source_match_metrics":{team:dict(counts) for team,counts in stats.items()},
                "match_event_count":len(events),
                "prematch_availability_verified":False,
                "allowed_for_same_match_prediction":False})
        except Exception as exc:
            errors.append({"external_match_id":item["external_match_id"],"error":str(exc)})
    output=ROOT/"data/statsbomb_linked_event_metrics.json"
    output.write_text(json.dumps({"retrieved_at":datetime.now(timezone.utc).isoformat(),
       "notice":"Observed post-match events only; cannot be used as same-match prematch inputs.",
       "records":rows,"errors":errors},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"linked_fixtures":len(links),"events_imported":len(rows),
       "errors":len(errors),"prematch_verified":0},indent=2))
if __name__=="__main__":run()
