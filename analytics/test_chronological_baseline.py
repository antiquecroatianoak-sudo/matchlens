"""Run a chronologically selected, results-only baseline with per-day 25% quota.

This is a baseline, not a 14-factor model. Selection does not look at future
candidate confidence scores. The base model itself excludes previous-day data.
"""
import json
from collections import defaultdict
from analytics.test_normalized_archive import run

def main():
    baseline=run()
    by_day=defaultdict(list)
    for p in baseline["predictions"]:
        by_day[p["date"]].append(p)
    selected=[]
    for day,items in sorted(by_day.items()):
        # A conservative cap from eligible candidates, not all fixtures.
        quota=len(items)//4
        selected.extend(sorted(items,key=lambda p:(-p["confidence"],p["match_id"]))[:quota])
    result={"label":"CHRONOLOGICAL RESULTS-ONLY BASELINE (NOT ALL-FACTOR)",
            "total_matches":baseline["matches"],"leagues":baseline["leagues"],
            "eligible":baseline["eligible"],"selected":len(selected),
            "correct":sum(int(p["correct"]) for p in selected),
            "accuracy":sum(int(p["correct"]) for p in selected)/len(selected) if selected else None,
            "limitations":"No verified 14-factor inputs; selection uses same-date eligible fixtures and is not a fully independent trained walk-forward model."}
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
