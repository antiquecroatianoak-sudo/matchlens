"""Restore original historical OpenFootball source files, without inventing match timestamps.

Usage: python -m ingestion.restore_manifest_sources
Only downloads sources declared in data/source-manifest.json. Raw files are kept
separate from normalized match data; this command never runs a predictive test.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "source-manifest.json"
DEST = ROOT / "data" / "upstream_openfootball"


def restore(limit=None, reconcile=False):
    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))["source_files"]
    DEST.mkdir(parents=True, exist_ok=True)
    results = {"downloaded": [], "existing": [], "failed": []}
    changed = False
    for item in sources[:limit]:
        name = item["file"]
        if Path(name).name != name or not name.endswith(".json"):
            results["failed"].append({"file": name, "reason": "unsafe filename"})
            continue
        url = item["url"]
        prefix = "https://github.com/openfootball/football.json/blob/"
        if not url.startswith(prefix):
            results["failed"].append({"file": name, "reason": "unapproved source"})
            continue
        raw_url = "https://raw.githubusercontent.com/openfootball/football.json/" + url[len(prefix):]
        path = DEST / name
        try:
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]:
                results["existing"].append(name)
                continue
            with urlopen(raw_url, timeout=25) as response:
                payload = response.read(4_000_001)
            if len(payload) > 4_000_000:
                raise ValueError("source file too large")
            digest = hashlib.sha256(payload).hexdigest()
            if digest != item["sha256"] and not reconcile:
                raise ValueError(f"SHA256 mismatch: expected={item['sha256']} actual={digest} url={raw_url}")
            parsed = json.loads(payload)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("matches"), list):
                raise ValueError("unexpected source format")
            if reconcile and digest != item["sha256"]:
                item["sha256"] = digest
                item["verified_source_url"] = raw_url
                changed = True
            path.write_bytes(payload)
            results["downloaded"].append(name)
        except (OSError, ValueError, KeyError) as exc:
            results["failed"].append({"file": name, "reason": str(exc)})
    if changed:
        MANIFEST.write_text(json.dumps({"source_files": sources}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--reconcile", action="store_true", help="Explicitly trust current upstream bytes after schema validation; update manifest checksums")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    print(json.dumps(restore(args.limit, reconcile=args.reconcile), indent=2, ensure_ascii=False))
