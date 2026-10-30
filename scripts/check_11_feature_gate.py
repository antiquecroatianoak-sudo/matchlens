"""Check that historical test records have >=11 populated prematch feature values."""
import argparse,csv,json,math
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="out/feature_gate.json")
    p.add_argument("--min-features",type=int,default=11)
    p.add_argument("--min-matches",type=int,default=1000)
    args=p.parse_args()
    src=Path(args.input)
    if src.suffix==".csv":
        with src.open(encoding="utf-8-sig",newline="") as f: records=list(csv.DictReader(f))
    else:
        data=json.loads(src.read_text(encoding="utf-8"))
        records=data["matches"] if isinstance(data,dict) else data
    reserved={"match_id","date","kickoff","league","season","home","away","home_id","away_id","home_goals","away_goals","source"}
    eligible=0
    counts=[]
    for row in records:
        features=row.get("features")
        if not isinstance(features,dict):
            features={k:v for k,v in row.items() if k not in reserved}
        populated=sum(v is not None and v!="" and not (isinstance(v,float) and not math.isfinite(v)) for v in features.values())
        counts.append(populated)
        if populated>=args.min_features:eligible+=1
    report={"records":len(records),"eligible":eligible,"min_features":args.min_features,
            "min_matches":args.min_matches,"min_observed":min(counts) if counts else 0,
            "max_observed":max(counts) if counts else 0,
            "pass":eligible>=args.min_matches,
            "warning":"Checks field presence only. Timestamp availability and feature provenance require separate validation; not proof of leakage-free data."}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report))
    if not report["pass"]:raise SystemExit("Insufficient records with >=11 populated feature fields")
if __name__=="__main__":main()
