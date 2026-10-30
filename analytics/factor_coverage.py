"""Offline coverage report for accepted external factors, not model accuracy."""
from collections import Counter, defaultdict
from .factor_snapshot_import import read_factor_jsonl


def coverage_report(path, *, approved_sources, as_of, expected_match_ids):
    """Measure accepted data coverage over a caller-supplied candidate match set.

    A factor's coverage denominator includes all expected matches, never only
    matches where the external provider happens to have a record.
    """
    expected = set(expected_match_ids)
    if not expected:
        raise ValueError("expected_match_ids must be nonempty")
    result = read_factor_jsonl(path, approved_sources=approved_sources, as_of=as_of)
    by_factor = defaultdict(set)
    outside = 0
    for row in result["accepted"]:
        if row["match_id"] not in expected:
            outside += 1
        else:
            by_factor[row["factor"]].add(row["match_id"])
    counts = Counter(error for row in result["rejected"] for error in row["errors"])
    return {
        "expected_matches": len(expected),
        "accepted_records": result["accepted_count"],
        "rejected_records": result["rejected_count"],
        "accepted_outside_expected": outside,
        "rejection_reasons": dict(sorted(counts.items())),
        "factor_coverage": {
            factor: {"matches": len(matches), "fraction": len(matches) / len(expected)}
            for factor, matches in sorted(by_factor.items())
        },
        "note": "Coverage only; no factor is trained, activated or proven predictive.",
    }
