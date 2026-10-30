"""Run offline StatsBomb research reconciliation from local JSON files.

Example:
 python -m scripts.audit_statsbomb_reconciliation \
   --provider data/statsbomb_pilot/matches.json \
   --canonical canonical-fixtures.json --team-map reviewed-team-map.json \
   --output data/statsbomb_pilot/reconciliation-audit.json

No provider download, production database writes, or inferred team identities.
"""
import argparse
import json
from pathlib import Path
from analytics.statsbomb_reconcile import reconcile_statsbomb_matches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--team-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("Refusing to overwrite an existing audit")
    provider = json.loads(Path(args.provider).read_text(encoding="utf-8"))
    canonical = json.loads(Path(args.canonical).read_text(encoding="utf-8"))
    mapping_raw = json.loads(Path(args.team_map).read_text(encoding="utf-8"))
    if not isinstance(provider, list) or not isinstance(canonical, list) or not isinstance(mapping_raw, dict):
        parser.error("Expected provider and canonical arrays and reviewed team-map object")
    # JSON object keys are strings; StatsBomb team IDs are numeric.
    mapping = {int(key): value for key, value in mapping_raw.items()}
    result = reconcile_statsbomb_matches(provider, canonical, mapping)
    result["provider_match_count"] = len(provider)
    result["canonical_match_count"] = len(canonical)
    result["coverage_of_provider"] = result["paired_count"] / len(provider) if provider else 0.0
    result["coverage_of_canonical"] = result["paired_count"] / len(canonical) if canonical else 0.0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("provider_match_count", "canonical_match_count", "paired_count", "quarantined_count", "coverage_of_provider", "coverage_of_canonical")}, indent=2))


if __name__ == "__main__":
    main()
