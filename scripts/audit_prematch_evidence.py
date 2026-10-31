"""Audit whether a historical fixture source can certify pre-match readiness.

OpenFootball day-only dates and final scores support retrospective evaluation,
but do not establish prediction timestamps, executable odds, or 11 features.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def audit(folder):
    counts=Counter()
    by_league={}
    for path in sorted(Path(folder).glob("*.json")):
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            matches=data["matches"]
            if not isinstance(matches,list):
                raise ValueError("matches must be a list")
        except (ValueError, KeyError, TypeError) as exc:
            counts["invalid_files"]+=1
            continue
        league=path.name[8:-5]
        stats=by_league.setdefault(league,Counter())
        counts["files"]+=1
        for m in matches:
            counts["fixtures"]+=1
            stats["fixtures"]+=1
            if m.get("round") not in (None,""):
                counts["round_labels"]+=1
                stats["round_labels"]+=1
            if m.get("date"):
                counts["dates"]+=1
            # Source fixtures do not contain archived prediction snapshots;
            # never infer those from full-time results or file modification time.
            if isinstance(m.get("prediction_created_at"),str) and m.get("prediction_created_at"):
                counts["prediction_timestamp_claims"]+=1
            if isinstance(m.get("bookmaker_odds"),dict) and m.get("bookmaker_odds"):
                counts["odds_claims"]+=1
            if isinstance(m.get("prematch_factors"),dict) and len(m["prematch_factors"])>=11:
                counts["factor_claims_11_plus"]+=1
    return {
        "status":"research_source_audit_only",
        "source":"local restored historical fixture JSON",
        "counts":dict(counts),
        "by_league":{k:dict(v) for k,v in sorted(by_league.items())},
        "certified_complete_rounds":False,
        "timestamped_prematch_predictions_verified":False,
        "eleven_prematch_factors_verified":False,
        "historical_executable_odds_verified":False,
        "reason":"Fixture records alone cannot certify full league schedules, as-of prediction provenance, 11 verified factors or bookmaker odds."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=audit(args.folder)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
