"""Strict offline reconciliation of StatsBomb research matches to canonical fixtures.

Do not guess team identity from fuzzy names. An explicit, reviewed mapping is
required for each team. Conflicting and ambiguous matches stay quarantined.
"""
from collections import defaultdict
from datetime import date


def reconcile_statsbomb_matches(provider_matches, canonical_matches, team_map):
    """Return unique fixture pairs, unresolved rows and ambiguities.

    Canonical fixture rows: id, date (YYYY-MM-DD), home, away.
    Provider rows: match_id, match_date, home_team:{home_team_id},
    away_team:{away_team_id}.
    """
    canonical = defaultdict(list)
    for row in canonical_matches:
        canonical[(row["date"], str(row["home"]), str(row["away"]))].append(row["id"])
    paired, quarantined, seen_provider, seen_canonical = [], [], set(), set()
    for match in provider_matches:
        provider_id = match.get("match_id")
        if provider_id in seen_provider:
            quarantined.append({"provider_match_id": provider_id, "reason": "duplicate_provider_match"})
            continue
        seen_provider.add(provider_id)
        home_id = (match.get("home_team") or {}).get("home_team_id")
        away_id = (match.get("away_team") or {}).get("away_team_id")
        if home_id not in team_map or away_id not in team_map:
            quarantined.append({"provider_match_id": provider_id, "reason": "unmapped_team"})
            continue
        try:
            day = date.fromisoformat(match["match_date"]).isoformat()
        except (ValueError, TypeError, KeyError):
            quarantined.append({"provider_match_id": provider_id, "reason": "invalid_date"})
            continue
        key = (day, str(team_map[home_id]), str(team_map[away_id]))
        candidates = canonical.get(key, [])
        if len(candidates) != 1:
            quarantined.append({"provider_match_id": provider_id, "reason": "ambiguous_or_missing_fixture", "candidates": len(candidates)})
            continue
        if candidates[0] in seen_canonical:
            quarantined.append({"provider_match_id": provider_id, "reason": "duplicate_canonical_match"})
            continue
        seen_canonical.add(candidates[0])
        paired.append({"provider_match_id": provider_id, "canonical_match_id": candidates[0], "date": day})
    return {
        "paired": paired,
        "quarantined": quarantined,
        "paired_count": len(paired),
        "quarantined_count": len(quarantined),
        "note": "Research-only mapping; no production writes or predictive promotion.",
    }
