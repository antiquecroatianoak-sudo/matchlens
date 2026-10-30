"""Strict final-test gate: never substitute results-only tests for all-factor tests."""
import json
import sys
from analytics.audit_normalized_readiness import audit
from analytics.factor_source_registry import GROUPS

def check():
    report=audit()
    coverage=report["factor_coverage"]
    missing=[group for group in GROUPS if coverage[group]["verified_matches"]==0]
    ready=(report["ready_for_full_backtest"] and not missing)
    return {"final_test_started":ready,"final_test_completed":False,
            "all_factor_groups":len(GROUPS),
            "groups_without_verified_records":missing,
            "verified_kickoffs":report["verified_kickoffs"],
            "matches":report["matches"],
            "status":"READY_TO_RUN" if ready else "BLOCKED_MISSING_VERIFIED_PREMATCH_DATA",
            "reason":"A successful exploratory run is not a valid full-factor test."}

if __name__=="__main__":
    result=check()
    print(json.dumps(result,indent=2))
    sys.exit(0 if result["final_test_started"] else 2)
