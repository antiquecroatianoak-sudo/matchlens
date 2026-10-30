"""Deterministic, opt-in import of externally sourced factor snapshots.

No network fetches and no promotion to production prediction. Caller must
supply an approved source allowlist and an as-of timestamp.
"""
import json
from pathlib import Path
from .factor_intake import validate_factor


def read_factor_jsonl(path, *, approved_sources, as_of):
    """Read historical observations; reject unlicensed/late/ambiguous rows.

    Returns accepted records and detailed rejection reasons. Does not impute
    missing values, infer timestamps, or write to a production database.
    """
    from datetime import datetime, timezone

    if not approved_sources:
        raise ValueError("approved_sources must be nonempty")
    cutoff = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if cutoff.tzinfo is None:
        raise ValueError("as_of must include timezone")
    cutoff = cutoff.astimezone(timezone.utc)
    accepted, rejected, seen = [], [], set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rejected.append({"line": line_number, "errors": ["invalid_json"]})
                continue
            if not isinstance(row, dict):
                rejected.append({"line": line_number, "errors": ["not_object"]})
                continue
            errors = validate_factor(row)
            if row.get("source") not in approved_sources:
                errors.append("source_not_approved")
            if not errors:
                available = datetime.fromisoformat(row["available_at"].replace("Z", "+00:00"))
                prediction = datetime.fromisoformat(row["prediction_at"].replace("Z", "+00:00"))
                if prediction.astimezone(timezone.utc) > cutoff or available.astimezone(timezone.utc) > cutoff:
                    errors.append("after_as_of")
                key = (row["match_id"], row["factor"], row["source"], row["available_at"])
                if key in seen:
                    errors.append("duplicate_observation")
                if not errors:
                    seen.add(key)
            if errors:
                rejected.append({"line": line_number, "errors": errors})
            else:
                accepted.append(row)
    return {"accepted": accepted, "rejected": rejected, "accepted_count": len(accepted), "rejected_count": len(rejected)}
