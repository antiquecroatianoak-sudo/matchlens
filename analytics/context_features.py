"""As-of weather and pitch feature contracts for historical football predictions.

This module does not fetch data or claim model integration. Missing inputs remain None.
"""
from datetime import datetime, timezone
import math

WEATHER_FIELDS = ("temperature_c", "precipitation_mm", "wind_kmh", "humidity_pct")
PITCH_FIELDS = ("surface", "length_m", "width_m", "wetness", "snow_cover", "damage")

def _instant(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be ISO 8601 string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone required")
    return dt.astimezone(timezone.utc)

def context_features(record, cutoff, kickoff):
    """Return vetted pre-match features; never use observed weather as a forecast."""
    if record is None:
        return None
    if not isinstance(record, dict):
        raise ValueError("Record must be an object")
    cut, start = _instant(cutoff), _instant(kickoff)
    if cut >= start:
        raise ValueError("Prediction cutoff must precede kickoff")
    available = _instant(record["available_at"])
    issued = _instant(record["issued_at"])
    if available > cut or issued > cut or issued > available:
        return None
    if record.get("kind") not in ("weather_forecast", "pitch_report"):
        raise ValueError("Unsupported source kind")
    if not isinstance(record.get("source_id"), str) or not record["source_id"].strip():
        raise ValueError("Source ID required")
    fields = WEATHER_FIELDS if record["kind"] == "weather_forecast" else PITCH_FIELDS
    out = {}
    for field in fields:
        value = record.get(field)
        if value is not None and field in ("temperature_c", "precipitation_mm", "wind_kmh", "humidity_pct", "length_m", "width_m"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Invalid numeric value: " + field)
            if field in ("precipitation_mm", "wind_kmh", "humidity_pct", "length_m", "width_m") and value < 0:
                raise ValueError("Negative value: " + field)
            if field == "humidity_pct" and value > 100:
                raise ValueError("Humidity out of range")
        out[field] = value
    return {"kind": record["kind"], "source_id": record["source_id"], "available_at": record["available_at"], "features": out}
