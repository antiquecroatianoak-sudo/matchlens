"""Join historical football fixture round metadata to archived factor predictions."""
import argparse,json
from pathlib import Path
from analytics.backtest import load_matches

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/openfootball")
    p.add_argument("--predictions",required=True)
    p.add_argument("--output",default="out/round-predictions.jsonl")
    a=p.parse_args()
    rows,_=load_matches(a.data)
    lookup={r["id"]:r for r in rows}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    count=0;missing=0
    with Path(a.predictions).open(encoding="utf-8") as source,out.open("w",encoding="utf-8") as target:
        for line in source:
            if not line.strip():continue
            pred=json.loads(line);match=lookup.get(pred["id"])
            if match is None:missing+=1;continue
            target.write(json.dumps({"id":pred["id"],"league":match["league"],"season":match["season"],
                "round":match["round"],"date":match["date"],"prob":pred["prob"],"actual":pred["actual"]})+"\n")
            count+=1
    print(json.dumps({"joined":count,"missing":missing}))
    if not count or missing:raise SystemExit("Incomplete join")
if __name__=="__main__":main()
