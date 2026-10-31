"""Settle previously frozen forecasts using the authenticated MatchLens database endpoint."""
import json
from urllib.request import Request, urlopen
from scripts.sync_prospective_oidc import ENDPOINT, identity

def main():
    request=Request(ENDPOINT,data=b'{"action":"settle"}',method="POST",
                    headers={"Authorization":"Bearer "+identity(),"Content-Type":"application/json"})
    with urlopen(request,timeout=120) as response:
        result=json.load(response)
    if not isinstance(result.get("settled"),int):
        raise RuntimeError("Invalid settlement response")
    print("HISTORICAL PROSPECTIVE SETTLEMENT",result)

if __name__=="__main__":
    main()
