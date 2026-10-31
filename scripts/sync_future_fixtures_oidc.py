"""Persist verified OpenLigaDB fixtures through the existing restricted OIDC endpoint."""
import json
from pathlib import Path
from scripts.sync_prospective_oidc import identity, ENDPOINT
from urllib.request import Request, urlopen

def main():
    data=json.loads(Path("out/future-fixtures.json").read_text())
    rows=[f for f in data["fixtures"] if f["id"].startswith("openligadb:")]
    if not rows:
        raise SystemExit("No verified OpenLigaDB fixtures to persist")
    received=0
    for i in range(0,len(rows),100):
        batch=rows[i:i+100]
        payload=json.dumps({"action":"fixtures","fixtures":batch}).encode()
        req=Request(ENDPOINT,data=payload,method="POST",headers={"Authorization":"Bearer "+identity(),"Content-Type":"application/json"})
        with urlopen(req,timeout=90) as response:
            result=json.load(response)
        if result.get("received")!=len(batch):
            raise RuntimeError("Incomplete fixture sync")
        received+=result["received"]
    print("VERIFIED FUTURE FIXTURES PERSISTED",received)

if __name__=="__main__":
    main()
