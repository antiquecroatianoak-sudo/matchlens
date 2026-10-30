"""List missing historical result files from the existing source manifest; no backtest."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reconcile():
    manifest = json.loads((ROOT / "data" / "source-manifest.json").read_text(encoding="utf-8"))
    expected = {row["file"]: row for row in manifest["source_files"]}
    actual = {p.name for p in (ROOT / "data" / "openfootball").glob("*.json")}
    missing = sorted(set(expected) - actual)
    return {
        "manifest_files": len(expected),
        "local_files": len(actual),
        "missing_files": missing,
        "missing_source_urls": {name: expected[name]["url"] for name in missing},
        "untracked_local_files": sorted(actual - set(expected)),
        "historical_backtest_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(reconcile(), ensure_ascii=False, indent=2))
