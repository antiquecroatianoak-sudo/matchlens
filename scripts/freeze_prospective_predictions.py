"""Freeze prematch predictions and select top quarter only for independently certified full rounds."""
import json
import math
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

def certified_round_ids(league, season, round_id, created_at):
    """Return complete provider fixture IDs for a wholly future round, or None."""
    if league not in ("bl1", "bl2") or not str(round_id).isdigit():
        return None
    url = f"https://api.openligadb.de/getmatchdata/{league}/{season}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MatchLens/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            matches = json.load(response)
        if not isinstance(matches, list):
            return None
        matches = [m for m in matches if str((m.get("group") or {}).get("groupOrderID")) == str(round_id)]
        if not matches:
            return None
        ids = set()
        for m in matches:
            mid = m.get("matchID")
            kickoff_raw = m.get("matchDateTimeUTC")
            if not isinstance(mid, int) or not isinstance(kickoff_raw, str) or m.get("matchIsFinished") is not False:
                return None
            kickoff = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00"))
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)
            if kickoff.astimezone(timezone.utc) <= created_at:
                return None
            ids.add(f"openligadb:{mid}")
        return ids if len(ids) == len(matches) else None
    except (OSError, ValueError, TypeError, KeyError):
        return None

def select(rows, created_at, round_lookup=certified_round_ids):
    groups = {}
    for row in rows:
        kickoff = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
        if kickoff < created_at + timedelta(hours=1):
            continue
        probs = row.get("prob")
        if not isinstance(probs, dict) or not all(k in probs for k in ("home", "draw", "away")):
            continue
        values = [float(probs[k]) for k in ("home", "draw", "away")]
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in values) or abs(sum(values)-1) > 0.002:
            continue
        outcome = max(("home", "draw", "away"), key=lambda k: float(probs[k]))
        record = {**row, "predicted_outcome": outcome, "confidence": float(probs[outcome]),
                  "predicted_at_utc": created_at.isoformat(),
                  "selection_rule": "top_25_percent_per_league_round"}
        groups.setdefault((row["league"], row["season"], row["round"]), []).append(record)
    all_rows = []
    for (league, season, round_id), group in groups.items():
        group.sort(key=lambda r: (-r["confidence"], r["kickoff_utc"], r["id"]))
        expected = round_lookup(league, season, round_id, created_at)
        observed = [r["id"] for r in group]
        certified = expected is not None and len(observed) == len(set(observed)) and set(observed) == set(expected)
        count = max(1, math.ceil(len(group) / 4)) if certified else 0
        for index, row in enumerate(group):
            row["top25"] = index < count
            row["round_certified"] = certified
            row["selection_group_size"] = len(group)
            all_rows.append(row)
    return all_rows

def main():
    path = Path("out/upcoming-probabilities.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    created_at = datetime.now(timezone.utc)
    selected = select(rows, created_at)
    Path("out/prospective-predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected))
    rounds = {}
    for row in selected:
        key = (row["league"], str(row["season"]), str(row["round"]))
        group = rounds.setdefault(key, {"league": key[0], "season": key[1],
            "round": key[2], "scored": 0, "selected": 0, "certified": False})
        group["scored"] += 1
        group["selected"] += int(row["top25"])
        group["certified"] = bool(row["round_certified"])
    round_coverage = sorted(rounds.values(), key=lambda g: (g["league"], g["season"], g["round"]))
    Path("out/prospective-round-coverage.json").write_text(json.dumps(round_coverage, indent=2) + "\\n")
    summary = {"generated_at_utc": created_at.isoformat(), "scored": len(rows),
               "eligible": len(selected), "top25": sum(r["top25"] for r in selected),
               "certified_rounds": len({(r["league"],r["season"],r["round"]) for r in selected if r["round_certified"]}),
               "warning": "Top25 is only selected when the full independent OpenLigaDB round is covered."}
    Path("out/prospective-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("PROSPECTIVE SNAPSHOT", summary)

if __name__ == "__main__":
    main()
