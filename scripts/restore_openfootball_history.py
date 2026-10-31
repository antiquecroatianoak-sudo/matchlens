"""Restore permitted OpenFootball historical match JSON for the ten leagues."""
import json,urllib.request,time
from pathlib import Path

LEAGUES=("en.1","it.1","es.1","de.1","de.2","fr.1","pt.1","be.1","nl.1","tr.1","gr.1")
SEASONS=tuple(f"{year}-{str((year+1)%100).zfill(2)}" for year in range(2010,2026))
BASE="https://raw.githubusercontent.com/openfootball/football.json/master"
def main():
    folder=Path("data/openfootball");folder.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for season in SEASONS:
        for league in LEAGUES:
            url=f"{BASE}/{season}/{league}.json"
            target=folder/f"{season}.{league}.json"
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"MatchLensResearch/1.0"})
                with urllib.request.urlopen(req,timeout=18) as response:
                    raw=response.read()
                obj=json.loads(raw)
                if not isinstance(obj.get("matches"),list):raise ValueError("Missing matches array")
                target.write_bytes(raw)
                manifest.append({"season":season,"league":league,"matches":len(obj["matches"]),"status":"ok"})
            except Exception as exc:
                manifest.append({"season":season,"league":league,"status":"unavailable","error":str(exc)[:120]})
            print(manifest[-1],flush=True)
            time.sleep(.1)
    Path("out").mkdir(exist_ok=True)
    Path("out/source_restore.json").write_text(json.dumps(manifest,indent=2))
    print("Downloaded",sum(x["status"]=="ok" for x in manifest),"of",len(manifest),"season-league files")
if __name__=="__main__":main()
