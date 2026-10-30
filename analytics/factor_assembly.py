"""Deterministic pre-match feature assembly. All sources must carry observed-at time.
No retrospective data is silently treated as known before kickoff.
"""
from datetime import datetime, timezone

def instant(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None: raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)

def assemble(match, cutoff, required):
    t=instant(cutoff)
    if t>=instant(match["kickoff"]): raise ValueError("Cutoff must precede kickoff")
    features={}
    missing=[]
    for name in required:
        candidates=match.get("feature_records",{}).get(name,[])
        eligible=[r for r in candidates if r.get("value") is not None and
                  r.get("source_id") and r.get("available_at") and
                  instant(r["available_at"])<=t and
                  (not r.get("issued_at") or instant(r["issued_at"])<=t)]
        if eligible:
            chosen=max(eligible,key=lambda r:instant(r["available_at"]))
            features[name]={"value":chosen["value"],"source_id":chosen["source_id"],
                            "available_at":chosen["available_at"]}
        else:
            missing.append(name)
    return {"match_id":match["match_id"],"cutoff":cutoff,
            "features":features,"missing":missing,"complete":not missing}
