"""Normalize historical lineup and weather source records without future leakage.

No external API is contacted here. Feed only records from sources whose use is permitted.
"""
from datetime import datetime, timezone
from analytics.context_features import context_features

def _utc(value):
    if not isinstance(value, str):
        raise ValueError("ISO timestamp required")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("Timezone required")
    return t.astimezone(timezone.utc)

def lineup_features(record, cutoff, kickoff):
    """Confirmed lineups must have been publicly available at the prediction cutoff."""
    if record is None:
        return None
    if not isinstance(record, dict) or record.get("kind") != "confirmed_lineup":
        raise ValueError("Expected confirmed_lineup record")
    cut, kick = _utc(cutoff), _utc(kickoff)
    if cut >= kick:
        raise ValueError("Prediction cutoff must precede kickoff")
    if _utc(record["published_at"]) > cut or _utc(record["available_at"]) > cut:
        return None
    if _utc(record["published_at"]) > _utc(record["available_at"]):
        raise ValueError("Publication after availability")
    for key in ("source_id", "match_id", "team_id"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError("Missing identity: " + key)
    players = record.get("starting_player_ids")
    if not isinstance(players, list) or len(players) != 11 or any(not isinstance(p, str) or not p.strip() for p in players) or len(set(players)) != 11:
        raise ValueError("Exactly 11 distinct canonical starting player IDs required")
    return {"match_id": record["match_id"], "team_id": record["team_id"], "source_id": record["source_id"], "available_at": record["available_at"], "starting_player_ids": list(players)}

def prematch_context(weather, pitch, lineup, cutoff, kickoff):
    return {
        "weather": context_features(weather, cutoff, kickoff),
        "pitch": context_features(pitch, cutoff, kickoff),
        "lineup": lineup_features(lineup, cutoff, kickoff),
    }
