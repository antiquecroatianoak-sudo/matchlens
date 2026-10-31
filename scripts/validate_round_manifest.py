"""Fail-closed validation of independent complete-round fixture manifests.

A manifest must be supplied by a separately archived schedule source. This
validator never infers expected fixtures from the observed scored matches.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def validate(manifest, scored_ids):
    if not isinstance(manifest,dict) or not isinstance(manifest.get("rounds"),list):
        raise ValueError("manifest requires rounds list")
    results=[]
    for group in manifest["rounds"]:
        key={k:group.get(k) for k in ("league","season","round")}
        expected=group.get("scheduled_fixture_ids")
        source=group.get("schedule_source")
        archived=group.get("schedule_archived_at")
        if not all(isinstance(v,str) and v.strip() for v in key.values()):
            raise ValueError("missing league, season or round")
        if not isinstance(expected,list) or not expected or not all(isinstance(v,str) and v for v in expected):
            raise ValueError("expected fixture IDs required")
        if len(expected)!=len(set(expected)):
            raise ValueError("duplicate expected fixture IDs")
        if not isinstance(source,str) or not source.strip() or not isinstance(archived,str) or not archived.strip():
            raise ValueError("independent schedule source and archive timestamp required")
        observed=set(scored_ids.get((key["league"],key["season"],key["round"]),[]))
        missing=sorted(set(expected)-observed)
        unexpected=sorted(observed-set(expected))
        # Completeness of IDs is necessary but NOT sufficient for independent certification.
        results.append({**key,"expected":len(expected),"observed":len(observed),
            "missing_ids":missing,"unexpected_ids":unexpected,
            "matches_manifest":not missing and not unexpected,
            "certified_complete_round":False,
            "reason":"Schedule provenance and source independence require external verification."})
    return {"status":"research_only_unverified_schedule","rounds":results,
        "certified_complete_rounds":False}

def read_scored(path):
    grouped={}
    with open(path,encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():continue
            row=json.loads(line)
            if not row.get("round"):continue
            key=(row["league"],row["season"],row["round"])
            grouped.setdefault(key,[]).append(row["id"])
    for key,ids in grouped.items():
        if len(ids)!=len(set(ids)):
            raise ValueError("duplicate scored fixture IDs in "+repr(key))
    return grouped

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("manifest")
    p.add_argument("scored_predictions")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=validate(json.loads(Path(args.manifest).read_text()),read_scored(args.scored_predictions))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"rounds_checked":len(result["rounds"]),"status":result["status"]}))
