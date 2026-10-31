"""Prefer the two-season advanced model for each eligible fixture; retain explicitly labelled baseline fallback."""
import json
from pathlib import Path

def read_rows(path):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def combine(baseline, advanced):
    by_id = {row["id"]: row for row in baseline}
    for row in advanced:
        if row["id"] not in by_id and row.get("model") != "factor_search_v1_two_completed_seasons":
            continue
        if row.get("model") == "factor_search_v1_two_completed_seasons":
            by_id[row["id"]] = row
    return list(by_id.values())

def main():
    baseline = read_rows("out/upcoming-probabilities.jsonl")
    advanced = read_rows("out/upcoming-advanced-probabilities.jsonl")
    merged = combine(baseline, advanced)
    Path("out/upcoming-probabilities.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged))
    print("PRODUCTION PROSPECTIVE", {
        "advanced": sum(r["model"] == "factor_search_v1_two_completed_seasons" for r in merged),
        "baseline_fallback": sum(r["model"] == "historical_poisson_fallback_v1" for r in merged),
        "total": len(merged)})
    if not merged:
        raise SystemExit("No valid prospective predictions available")

if __name__ == "__main__":
    main()
