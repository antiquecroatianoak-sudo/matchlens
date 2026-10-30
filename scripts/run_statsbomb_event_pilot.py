"""Run a reproducible, read-only StatsBomb event/xG pilot on a saved sample.

The provider publishes post-match event files, so they are NOT same-match
prediction inputs. Outputs are research artifacts only; publication timestamps
must be verified independently before historical pre-match evaluation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from scripts.extract_statsbomb_features import extract

BASE = "https://raw.githubusercontent.com/hudl/open-data/master/data/events"


def run(sample_path, output_dir, *, max_matches=0):
    sample = json.loads(Path(sample_path).read_text(encoding="utf-8"))
    matches = sample["matches"]
    if max_matches < 0:
        raise ValueError("max_matches cannot be negative")
    selected = matches[:max_matches] if max_matches else matches
    rows, failures, provenance = [], [], []
    for match in selected:
        match_id = match["match_id"]
        try:
            request = Request(f"{BASE}/{match_id}.json", headers={"User-Agent": "MatchLens-StatsBomb-research/1.0"})
            with urlopen(request, timeout=30) as response:
                payload = response.read()
            events = json.loads(payload)
            if not isinstance(events, list):
                raise ValueError("events payload is not a list")
            extracted = extract(match_id, events)
            expected = {match["home_id"], match["away_id"]}
            actual = {r["team_id"] for r in extracted}
            if not expected.issubset(actual):
                raise ValueError("event team IDs do not match research sample")
            rows.extend(extracted)
            provenance.append({"match_id": match_id, "sha256": hashlib.sha256(payload).hexdigest(), "events": len(events)})
        except Exception as exc:
            failures.append({"match_id": match_id, "error": str(exc)})
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [
        ("team_xg.json", rows),
        ("event_provenance.json", provenance),
        ("audit.json", {
            "provider": "Hudl StatsBomb Open Data",
            "research_only": True,
            "matches_requested": len(selected),
            "matches_downloaded": len(provenance),
            "matches_failed": len(failures),
            "team_rows": len(rows),
            "failures": failures,
            "historical_prematch_ready": False,
            "reason": "Verified historical event publication timestamps and canonical team mapping not supplied",
        }),
    ]:
        destination = out / name
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite {destination}")
        destination.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"requested": len(selected), "downloaded": len(provenance), "failed": len(failures), "team_rows": len(rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="data/research/statsbomb_bundesliga_2023_24_sample.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-matches", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(run(args.sample, args.output_dir, max_matches=args.max_matches), indent=2))


if __name__ == "__main__":
    main()
