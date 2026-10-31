"""Send prospective snapshots through GitHub OIDC to a restricted MatchLens Edge Function."""
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
import os

ENDPOINT="https://jhsakrbcdjabxkgdalta.supabase.co/functions/v1/prospective-sync"
AUDIENCE="matchlens-prospective:jhsakrbcdjabxkgdalta"

def identity():
    url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]+"&audience="+quote(AUDIENCE,safe="")
    request=Request(url,headers={"Authorization":"Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]})
    with urlopen(request,timeout=30) as response:
        return json.load(response)["value"]

def upload(rows):
    token=identity()
    payload=json.dumps({"action":"freeze","predictions":rows},ensure_ascii=False).encode()
    request=Request(ENDPOINT,data=payload,method="POST",
                    headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urlopen(request,timeout=90) as response:
        result=json.load(response)
    if result.get("received")!=len(rows):
        raise RuntimeError("Incomplete prospective sync")
    return result

def main():
    path=Path("out/prospective-predictions.jsonl")
    rows=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not rows:
        print("PROSPECTIVE DATABASE SYNC: no eligible predictions; no upload")
        return
    received=inserted=0
    for start in range(0,len(rows),100):
        result=upload(rows[start:start+100])
        received+=result["received"];inserted+=result["inserted"]
    print("PROSPECTIVE DATABASE SYNC",{"received":received,"inserted_or_promoted":inserted,"submitted_top25":sum(bool(r.get("top25")) for r in rows)})
if __name__=="__main__":main()
