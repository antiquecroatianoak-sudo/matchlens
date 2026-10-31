"""Fail closed on publication readiness; historical research may still succeed."""
import argparse
import json
from pathlib import Path

REQUIRED_EVIDENCE = (
    "certified_complete_rounds",
    "timestamped_prematch_predictions",
    "eleven_verified_prematch_factors",
    "historical_executable_bookmaker_odds",
    "independent_unseen_prospective_holdout",
)

def assess(backtest, top25, evidence=None):
    if backtest.get("status") != "research_only" or top25.get("status") != "research_only":
        raise ValueError("Expected research-only input reports")
    matches = backtest.get("final_test", {}).get("matches")
    selected = top25.get("selected_observed_top_quarter")
    hits = top25.get("hits")
    if not isinstance(matches, int) or matches <= 0:
        raise ValueError("Missing test matches")
    if not isinstance(selected, int) or not 0 < selected <= matches:
        raise ValueError("Invalid selection count")
    if not isinstance(hits, int) or not 0 <= hits <= selected:
        raise ValueError("Invalid hit count")
    evidence = evidence or {}
    # An assertion is valid only with independently auditable proof; flags alone
    # cannot certify readiness.
    missing = [name for name in REQUIRED_EVIDENCE
               if not (isinstance(evidence.get(name), dict)
                       and evidence[name].get("verified") is True
                       and isinstance(evidence[name].get("source"), str)
                       and evidence[name]["source"].strip())]
    return {
        "status": "blocked_for_publication" if missing else "requires_manual_release_review",
        "live_predictions_enabled": False,
        "research_accuracy": hits / selected,
        "research_selected": selected,
        "research_hits": hits,
        "research_test_matches": matches,
        "missing_verification": missing,
        "warning": "Retrospective research is not a certified complete-round prospective forecast. This report never authorizes automatic publication."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("backtest")
    p.add_argument("top25")
    p.add_argument("--evidence")
    p.add_argument("--output", required=True)
    args=p.parse_args()
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    result=assess(load(args.backtest),load(args.top25),load(args.evidence) if args.evidence else None)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    main()
