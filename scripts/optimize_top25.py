"""Walk-forward threshold search on pre-match predictions. No production deployment.
CSV: kickoff, league, season, round, match_id, predicted_probability,
actual_correct, valid_parameters, round_complete, prediction_created_at.
Only predictions created before kickoff are eligible.
"""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from collections import defaultdict

def dt(s):
    value = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Timestamps must include timezone")
    return value.astimezone(timezone.utc)

def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kickoff = dt(row["kickoff"])
            created = dt(row["prediction_created_at"])
            if created >= kickoff:
                raise ValueError("Prediction generated at or after kickoff")
            p = float(row["predicted_probability"])
            actual = int(row["actual_correct"])
            if not math.isfinite(p) or not (0 <= p <= 1) or actual not in (0, 1):
                raise ValueError("Invalid probability or outcome")
            if int(row["valid_parameters"]) < 11:
                continue
            row["_p"], row["_y"], row["_time"] = p, actual, kickoff
            rows.append(row)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["league"],row["season"],row["round"])].append(row)
    eligible = []
    for key, group in groups.items():
        if any(r["round_complete"].lower() != "true" for r in group):
            continue
        ids = [r["match_id"] for r in group]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate match in {key}")
        eligible.append((max(r["_time"] for r in group), group))
    return sorted(eligible, key=lambda x: x[0])

def score(groups, threshold):
    hits = count = 0
    for _, group in groups:
        ranked = sorted(group, key=lambda r: (-r["_p"], r["match_id"]))
        chosen = ranked[:math.floor(len(group)*0.25)]
        hits += sum(r["_y"] for r in chosen)
        count += len(chosen)
    return {"hits": hits, "selected": count, "accuracy": hits/count if count else None}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--output",default="optimization-results.json")
    args=parser.parse_args()
    groups=load(args.csv)
    if len(groups) < 12:
        raise ValueError("At least 12 complete rounds required")
    split=int(len(groups)*0.7)
    train, holdout=groups[:split],groups[split:]
    if train[-1][0] >= holdout[0][0]:
        raise ValueError("Overlapping train/holdout timestamps")
    # Fixed 25% coverage: optimize only tie-break weights/model parameters upstream.\n    # Confidence thresholds are forbidden because they silently reduce coverage.\n    candidates=[0.0]
    minimum=sum(len(g)//4 for _,g in train)
    viable=[(t,score(train,t)) for t in candidates]
    viable=[(t,s) for t,s in viable if s["selected"] >= minimum]
    if not viable:
        raise ValueError("Insufficient training selections")
    threshold, training=max(viable,key=lambda pair:(pair[1]["accuracy"],pair[1]["selected"]))
    result={"selection_policy":"exact_top_quarter","threshold":threshold,"training":training,"holdout":score(holdout,threshold),"training_rounds":len(train),"holdout_rounds":len(holdout),"warning":"Research only. Holdout must not be reused for tuning; predictions must be truly pre-match."}
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
