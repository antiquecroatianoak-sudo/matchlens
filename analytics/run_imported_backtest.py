"""Run a reproducible baseline on real imported OpenFootball snapshots.

Usage: python -m analytics.run_imported_backtest
This does NOT claim to evaluate unavailable historical contextual factors.
"""
import json
from pathlib import Path
from analytics.historical_baseline import walk_forward

ROOT=Path(__file__).resolve().parents[1]
FILES=("en_2023_24.json","en_2024_25.json")
def load():
    rows=[]
    for name in FILES:
        payload=json.loads((ROOT/"data"/"openfootball"/name).read_text(encoding="utf-8"))
        assert payload["source"]=="openfootball/football.json"
        assert payload["source_blob_sha"]
        rows.extend(payload["matches"])
    return rows

def main():
    data=load()
    result=walk_forward(data,min_history=10,delay_days=2)
    evaluated=result["predictions"]
    # Explicit season membership from source manifest, not calendar-year matching.
    ids={r["match_id"] for r in json.loads((ROOT/"data"/"openfootball"/FILES[1]).read_text())["matches"]}
    test=[r for r in evaluated if r["match_id"] in ids and r["outcome"] is not None]
    n=len(test)
    accuracy=sum(max(range(3),key=lambda i:r["probabilities_1x2"][i])==r["outcome"] for r in test)/n if n else None
    brier=sum(sum((p-int(i==r["outcome"]))**2 for i,p in enumerate(r["probabilities_1x2"])) for r in test)/n if n else None
    over_hits=0
    actual={r["match_id"]:r for r in data}
    for r in test:
        m=actual[r["match_id"]]
        over_hits+=int((r["probability_over25"]>=.5)==(m["home_goals"]+m["away_goals"]>2))
    print(json.dumps({"dataset":"OpenFootball EPL 2023-24 train history / 2024-25 retrospective test","tested":n,"accuracy_1x2":accuracy,"brier_1x2":brier,"accuracy_over25":over_hits/n if n else None,"warning":"date-only records, two-day assumed publication delay; not full-factor backtest"},indent=2))
if __name__=="__main__": main()
