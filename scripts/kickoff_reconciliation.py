"""Conservative cross-provider kickoff reconciliation for MatchLens.

Inputs must contain an independently verified timezone-aware ISO timestamp.
This module does not scrape providers or infer timezones from fixture dates.
"""
from datetime import datetime, timezone
from collections import defaultdict
from typing import Iterable


def reconcile_kickoffs(records: Iterable[dict], minimum_sources: int = 2) -> dict:
    """Return accepted UTC fixtures and rejected groups with explicit reasons.

    Record keys: competition, home, away, source, kickoff_iso.
    A fixture is accepted only when at least minimum_sources distinct sources
    agree on the UTC kickoff instant. Unknown/naive timestamps are rejected.
    """
    grouped = defaultdict(list)
    rejected = []
    for record in records:
        try:
            key = tuple(str(record[k]).strip().casefold() for k in
                        ("competition", "home", "away"))
            source = str(record["source"]).strip()
            timestamp = str(record["kickoff_iso"]).strip()
            if not source or not all(key):
                raise ValueError("missing identity or source")
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError("timezone missing")
            utc = dt.astimezone(timezone.utc).isoformat()
            grouped[key].append((source, utc))
        except (KeyError, ValueError, TypeError) as exc:
            rejected.append({"record": record, "reason": str(exc)})
    accepted = []
    for key, entries in grouped.items():
        by_time = defaultdict(set)
        for source, utc in entries:
            by_time[utc].add(source)
        qualified = [(utc, sources) for utc, sources in by_time.items()
                     if len(sources) >= minimum_sources]
        if len(qualified) != 1 or len(by_time) != 1:
            rejected.append({"fixture": key, "reason": "conflicting or insufficient independent sources",
                             "sources": len({s for s, _ in entries})})
            continue
        utc, sources = qualified[0]
        accepted.append({"competition": key[0], "home": key[1],
                         "away": key[2], "kickoff_utc": utc,
                         "sources": sorted(sources)})
    return {"accepted": accepted, "rejected": rejected}
