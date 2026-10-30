"""Recover three missing OpenFootball 2023/24 seasons from documented TXT sources."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from analytics.import_upstream import parse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "2023-24-be.1.json": "https://raw.githubusercontent.com/openfootball/belgium/master/2023-24/be1.txt",
    "2023-24-gr.1.json": "https://raw.githubusercontent.com/openfootball/europe/master/greece/2023-24_gr1.txt",
    "2023-24-tr.1.json": "https://raw.githubusercontent.com/openfootball/europe/master/turkey/2023-24_tr1.txt",
}

def run():
    manifest_path = ROOT / "data/source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {item["file"]: item for item in manifest["source_files"]}
    destination = ROOT / "data/upstream_openfootball"
    destination.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, url in SOURCES.items():
        with urlopen(url, timeout=30) as response:
            source = response.read(1000000)
        rows = parse(source.decode("utf-8-sig"), "2023-24")
        if len(rows) < 100:
            raise ValueError(f"Missing matches: {name}")
        payload = json.dumps({"name": name, "matches": rows, "source": url},
                             ensure_ascii=False, indent=2).encode("utf-8")
        (destination / name).write_bytes(payload)
        entries[name]["sha256"] = hashlib.sha256(payload).hexdigest()
        entries[name]["verified_source_url"] = url
        counts[name] = len(rows)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts))
    return counts

if __name__ == "__main__":
    run()
