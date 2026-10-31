"""Settle previously timestamped research predictions against finished OpenLigaDB games.

Never regenerate a prediction after kickoff or treat missing final scores as losses.
"""
import json
import urllib.request
from pathlib import Path

BASE="https://api.openligadb.de/getmatchdata"

def settle(record, match):
    if not record["id"].startswith("openligadb:"):
        return {"id":record["id"],"status":"unsupported_provider"}
    if not match or not match.get("matchIsFinished"):
        return {"id":record["id"],"status":"pending"}
    results=[r for r in (match.get("matchResults") or []) if r.get("resultTypeID")==2]
    if len(results)!=1:
        return {"id":record["id"],"status":"missing_unambiguous_final_score"}
    result=results[0]
    home,away=result.get("pointsTeam1"),result.get("pointsTeam2")
    if not isinstance(home,int) or not isinstance(away,int) or home<0 or away<0:
        return {"id":record["id"],"status":"invalid_final_score"}
    actual="home" if home>away else ("away" if away>home else "draw")
    prediction=str(record["predicted_outcome"])
    if prediction not in ("home", "draw", "away"):
        return {"id":record["id"],"status":"invalid_predicted_outcome"}
    return {"id":record["id"],"status":"settled",
            "score_home":home,"score_away":away,"actual_outcome":actual,
            "predicted_outcome":prediction,"correct":prediction==actual}

def main():
    source=Path("out/prospective-predictions.jsonl")
    records=[json.loads(x) for x in source.read_text().splitlines() if x.strip()]
    output=[]
    for row in records:
        if not row["id"].startswith("openligadb:"):
            output.append(settle(row,None));continue
        match_id=row["id"].split(":",1)[1]
        if not match_id.isdecimal():
            output.append({"id":row["id"],"status":"invalid_match_id"});continue
        try:
            request=urllib.request.Request(f"{BASE}/{match_id}",headers={"User-Agent":"MatchLens/1.0"})
            with urllib.request.urlopen(request,timeout=15) as response:
                match=json.load(response)
            output.append(settle(row,match))
        except Exception as exc:
            output.append({"id":row["id"],"status":"provider_error","error":str(exc)[:120]})
    target=Path("out/prospective-settlement.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    finished=[r for r in output if r["status"]=="settled"]
    target.write_text(json.dumps({"settlements":output,
        "verified_accuracy":(sum(r["correct"] for r in finished)/len(finished) if finished else None),
        "settled_count":len(finished),
        "warning":"Accuracy covers only independently finished matches in this snapshot."},indent=2)+"\n")
    print("SETTLEMENT CHECK",len(output),"records")
if __name__=="__main__":main()
