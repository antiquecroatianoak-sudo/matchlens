"""Validation gate for adding timestamped external prediction factors.

Research infrastructure only: this module does not fetch data, claim a source is
licensed, or promote a feature into the live model.
"""
from datetime import datetime, timezone

REQUIRED = ("match_id", "factor", "value", "source", "observed_at", "available_at", "prediction_at")

def validate_factor(record):
    """Return errors; never silently replace missing historical evidence with zero."""
    errors = [f"missing:{key}" for key in REQUIRED if record.get(key) is None]
    if errors:
        return errors
    if not isinstance(record["source"], str) or not record["source"].strip():
        errors.append("source_required")
    if not isinstance(record["factor"], str) or not record["factor"].strip():
        errors.append("factor_required")
    parsed = {}
    for key in ("observed_at", "available_at", "prediction_at"):
        try:
            raw = record[key]
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("timezone required")
            parsed[key] = stamp.astimezone(timezone.utc)
        except (TypeError, ValueError, AttributeError):
            errors.append(f"invalid_timestamp:{key}")
    if len(parsed) == 3:
        if parsed["observed_at"] > parsed["available_at"]:
            errors.append("observation_after_availability")
        if parsed["available_at"] >= parsed["prediction_at"]:
            errors.append("not_available_before_prediction")
    return errors

def accepted_factors(records):
    """Separate accepted records from rejected records and their reasons."""
    accepted, rejected = [], []
    for record in records:
        errors = validate_factor(record)
        if errors:
            rejected.append({"record": record, "errors": errors})
        else:
            accepted.append(record)
    return {"accepted": accepted, "rejected": rejected}
