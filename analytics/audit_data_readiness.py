"""Audit historical result coverage without running a predictive backtest.

Run: python -m analytics.audit_data_readiness
This gate deliberately fails if required pre-match factor snapshots are absent.
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "lineups", "injuries", "suspensions", "xg", "weather_forecast",
    "pitch_condition", "rest_and_travel", "coaches", "player_roles",
    "formations", "motivation",
)

def audit():
    files = sorted((ROOT / "data" / "openfootball").glob("*.json"))
    leagues = defaultdict(lambda: {"matches": 0, "seasons": set()})
    ids = set()
    duplicate_ids = 0
    invalid = 0
    for file in files:
        obj = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or not isinstance(obj.get("matches"), list):
            continue
        league = str(obj.get("league") or "unknown")
        season = str(obj.get("season") or "unknown")
        for match in obj["matches"]:
            if not isinstance(match, dict) or match.get("home_goals") is None or match.get("away_goals") is None:
                invalid += 1
                continue
            key = str(match.get("match_id") or "")
            if not key or key in ids:
                duplicate_ids += 1
            ids.add(key)
            leagues[league]["matches"] += 1
            leagues[league]["seasons"].add(season)
    factor_dir = ROOT / "data" / "historical_factors"
    coverage = {}
    for factor in REQUIRED:
        path = factor_dir / (factor + ".jsonl")
        count = 0
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("match_id") in ids and row.get("source_id") and row.get("available_at"):
                    count += 1
        coverage[factor] = {"verified_records": count, "complete": count >= len(ids) and len(ids) > 0}
    ready = (len(leagues) >= 10 and duplicate_ids == 0 and invalid == 0
             and all(v["complete"] for v in coverage.values()))
    return {"historical_backtest_executed": False, "ready_for_full_backtest": ready,
            "leagues": {k: {"matches": v["matches"], "seasons": sorted(v["seasons"])}
                        for k, v in sorted(leagues.items())},
            "total_matches": sum(v["matches"] for v in leagues.values()),
            "duplicate_ids": duplicate_ids, "invalid_rows": invalid,
            "required_factor_coverage": coverage,
            "warning": "Counts are structural only; actual temporal validity, licenses and team mapping still require validation."}

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
