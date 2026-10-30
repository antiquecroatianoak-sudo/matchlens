"""Import archived OpenFootball fixtures through a GitHub OIDC-protected MatchLens Edge Function."""
import json, os, time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from sync_openfootball_supabase import fixture_rows

ENDPOINT="https://jhsakrbcdjabxkgdalta.supabase.co/functions/v1/fixture-sync"
AUDIENCE="matchlens-fixtures:jhsakrbcdjabxkgdalta"
def identity():
    url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]+"&audience="+quote(AUDIENCE,safe="")
    req=Request(url,headers={"Authorization":"Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]})
    with urlopen(req,timeout=30) as response:
        return json.load(response)["value"]
def upload(rows):
    payload=json.dumps({"action":"sync","fixtures":rows},ensure_ascii=False).encode()
    for attempt in range(5):
        token=identity()
        req=Request(ENDPOINT,data=payload,method="POST",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
        try:
            with urlopen(req,timeout=90) as response:
                result=json.load(response)
            if result.get("received")!=len(rows):
                raise RuntimeError("Incomplete batch confirmation")
            return result
        except HTTPError as exc:
            detail=exc.read(300).decode("utf-8","replace")
            if exc.code not in (429,500,502,503,504) or attempt==4:
                raise RuntimeError(f"Fixture sync HTTP {exc.code}: {detail}") from exc
        except (URLError,TimeoutError):
            if attempt==4: raise
        time.sleep(2**attempt)
def main():
    seen=set();batch=[];received=inserted=0
    for row in fixture_rows():
        if row["id"] in seen:continue
        seen.add(row["id"]);batch.append(row)
        if len(batch)==500:
            result=upload(batch);received+=result["received"];inserted+=result["inserted"]
            print("Processed",received,"inserted",inserted,flush=True);batch=[]
    if batch:
        result=upload(batch);received+=result["received"];inserted+=result["inserted"]
    print("Complete: processed",received,"new",inserted,flush=True)
if __name__=="__main__":main()
