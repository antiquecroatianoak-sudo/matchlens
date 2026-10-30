"""Build pre-match rolling xG features from previously published match events.

Input records must be independently reconciled to canonical match/team IDs.
A prior match's xG is not available at kickoff; require a verified published_at.
No network access, source rights assertions, or production writes.
"""
from collections import defaultdict
from datetime import datetime, timezone
import math


def _utc(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timestamp must have timezone")
    return stamp.astimezone(timezone.utc)


def prior_xg_features(history, fixtures, *, min_history=3, max_history=10):
    """Return eligible factor rows and omissions; never use target-match events.

    history: match_id, team_id, xg, match_end_at, published_at, source.
    fixtures: match_id, team_id, prediction_at.
    The caller is responsible for validated canonical identities and licensing.
    """
    if min_history < 1 or max_history < min_history:
        raise ValueError("invalid history window")
    by_team = defaultdict(list)
    rejected = []
    seen = set()
    for index, row in enumerate(history):
        try:
            if not row.get("source") or not row.get("match_id") or not row.get("team_id"):
                raise ValueError("missing provenance or identity")
            xg = float(row["xg"])
            if not math.isfinite(xg) or not 0 <= xg < 100:
                raise ValueError("invalid xg")
            ended = _utc(row["match_end_at"])
            published = _utc(row["published_at"])
            if published < ended:
                raise ValueError("publication precedes match end")
            identity = (str(row["match_id"]), str(row["team_id"]))
            if identity in seen:
                raise ValueError("duplicate team-match observation")
            seen.add(identity)
            by_team[row["team_id"]].append((published, ended, row["match_id"], xg, row["source"]))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            rejected.append({"index": index, "reason": str(exc)})
    output, missing = [], []
    for fixture in fixtures:
        try:
            prediction = _utc(fixture["prediction_at"])
            match_id, team_id = fixture["match_id"], fixture["team_id"]
            eligible = sorted(
                (r for r in by_team.get(team_id, ()) if r[0] < prediction and r[1] < prediction and r[2] != match_id),
                key=lambda r: (r[0], r[2]),
            )[-max_history:]
            if len(eligible) < min_history:
                missing.append({"match_id": match_id, "team_id": team_id, "reason": "insufficient_verified_prior_matches", "count": len(eligible)})
                continue
            # Use most recent evidence timestamp, never infer it from fixture date.
            output.append({
                "match_id": match_id, "team_id": team_id, "factor": "prior_matches_rolling_xg",
                "value": sum(r[3] for r in eligible) / len(eligible),
                "source": "derived:" + ",".join(sorted({r[4] for r in eligible})),
                "observed_at": max(r[1] for r in eligible).isoformat(),
                "available_at": max(r[0] for r in eligible).isoformat(),
                "prediction_at": prediction.isoformat(),
                "history_count": len(eligible),
            })
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            missing.append({"match_id": fixture.get("match_id"), "reason": "invalid_fixture:" + str(exc)})
    return {"factors": output, "missing": missing, "rejected_history": rejected}
