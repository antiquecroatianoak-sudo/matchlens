"""Export a research model selected using tuning data only.

analytics.backtest searches configurations on its tuning season, calibrates on
a separate season, and reports later seasons without using them for selection.
This file exports the fitted configuration; it does not deploy live tips.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

def export(source):
    report=json.loads(Path(source).read_text(encoding="utf-8"))
    if report.get("status")!="research_only":
        raise ValueError("Only research reports can be exported")
    splits=report["splits"]
    periods=[set(splits[k]) for k in ("warmup","tuning","calibration","test")]
    if any(periods[i]&periods[j] for i in range(4) for j in range(i+1,4)):
        raise ValueError("Training and holdout seasons overlap")
    config=report["selected_config"]
    if config not in [trial["config"] for trial in report["trials"]]:
        raise ValueError("Selected config missing from training candidates")
    return {
        "status":"research_only_not_deployed",
        "trained_at":datetime.now(timezone.utc).isoformat(),
        "method":"historical chronological hyperparameter selection",
        "selected_config":config,
        "configurations_evaluated":report["configurations_tested"],
        "training_seasons":splits["warmup"]+splits["tuning"],
        "calibration_seasons":splits["calibration"],
        "evaluation_seasons_not_used_for_training":splits["test"],
        "selection_metric":report["selection_metric"],
        "note":"Research model artifact; requires independently validated future rounds and verified prematch features before live deployment."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("backtest")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=export(a.backtest)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
