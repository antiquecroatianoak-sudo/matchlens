"""Build isolated research SQLite DB and chronological baseline report (stdlib only)."""
import argparse, json, math, sqlite3
from collections import defaultdict
from pathlib import Path

def run(source, destination, report_path):
    rows=json.loads(Path(source).read_text(encoding="utf-8"))["matches"]
    ids=[int(x["match_id"]) for x in rows]
    if len(ids)!=len(set(ids)): raise ValueError("Duplicate match IDs")
    rows=sorted(rows,key=lambda x:(x["date"],x["match_id"]))
    dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(dest))
    db.execute("""CREATE TABLE IF NOT EXISTS research_matches (
        match_id INTEGER PRIMARY KEY, match_date TEXT NOT NULL,
        home_id INTEGER NOT NULL, away_id INTEGER NOT NULL,
        home_name TEXT NOT NULL, away_name TEXT NOT NULL,
        home_goals INTEGER NOT NULL, away_goals INTEGER NOT NULL,
        source TEXT NOT NULL)""")
    db.execute("DELETE FROM research_matches")
    for m in rows:
        db.execute("INSERT INTO research_matches VALUES (?,?,?,?,?,?,?,?,?)",
                   (m["match_id"],m["date"],m["home_id"],m["away_id"],m["home"],m["away"],m["home_goals"],m["away_goals"],"StatsBomb open-data Bundesliga 2023/24 partial"))
    db.commit()
    assert db.execute("SELECT count(*) FROM research_matches").fetchone()[0]==len(rows)
    db.close()
    ratings=defaultdict(lambda:1500.0)
    results=[]
    # Warmup only; this tiny, incomplete sample is not a valid final test.
    for i,m in enumerate(rows):
        home,away=m["home_id"],m["away_id"]
        p=1/(1+10**((ratings[away]-ratings[home]-65)/400))
        outcome=1.0 if m["home_goals"]>m["away_goals"] else (0.5 if m["home_goals"]==m["away_goals"] else 0.0)
        if i>=10:
            choice="home" if p>=0.5 else "away"
            hit=(choice=="home" and outcome==1.0) or (choice=="away" and outcome==0.0)
            results.append({"match_id":m["match_id"],"date":m["date"],"pick":choice,"correct":bool(hit)})
        delta=20*(outcome-p)
        ratings[home]+=delta
        ratings[away]-=delta
    correct=sum(x["correct"] for x in results)
    report={"source_rows":len(rows),"db_rows":len(rows),"test_predictions":len(results),
            "correct":correct,"accuracy":correct/len(results) if results else None,
            "status":"exploratory_only","note":"Partial selected sample; no full-round 25% test, no market odds, no independent holdout. Never claim production accuracy.",
            "predictions":results}
    out=Path(report_path);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="predictions"}))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/research/statsbomb_bundesliga_2023_24_sample.json")
    p.add_argument("--db",default="out/matchlens_research.sqlite")
    p.add_argument("--report",default="out/research_backtest.json")
    a=p.parse_args()
    run(a.source,a.db,a.report)
