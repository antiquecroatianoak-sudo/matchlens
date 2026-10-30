"""Create SQLite schema for all fourteen pre-match parameter groups.

Usage: python -m analytics.create_factor_database [database_path]
The schema is intentionally empty until independently sourced observations arrive.
"""
import sqlite3
import sys
from pathlib import Path
from analytics.factor_source_registry import GROUPS

def create(path):
    db=sqlite3.connect(str(path))
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS fixtures(
      match_id TEXT PRIMARY KEY,
      league_season_file TEXT NOT NULL,
      match_date TEXT NOT NULL,
      home_team TEXT NOT NULL,
      away_team TEXT NOT NULL,
      kickoff_at TEXT,
      kickoff_verified INTEGER NOT NULL DEFAULT 0 CHECK(kickoff_verified IN (0,1))
    );
    CREATE TABLE IF NOT EXISTS source_documents(
      source_id TEXT PRIMARY KEY,
      source_url TEXT,
      retrieved_at TEXT,
      published_at TEXT,
      license_note TEXT,
      content_sha256 TEXT
    );
    CREATE TABLE IF NOT EXISTS factor_groups(
      group_name TEXT PRIMARY KEY,
      description TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS observations(
      observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
      match_id TEXT NOT NULL REFERENCES fixtures(match_id),
      group_name TEXT NOT NULL REFERENCES factor_groups(group_name),
      source_id TEXT NOT NULL REFERENCES source_documents(source_id),
      available_at TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      temporal_verified INTEGER NOT NULL DEFAULT 0 CHECK(temporal_verified IN (0,1)),
      UNIQUE(match_id,group_name,source_id,available_at)
    );
    CREATE INDEX IF NOT EXISTS observations_by_match_group
      ON observations(match_id,group_name,temporal_verified);
    CREATE TABLE IF NOT EXISTS quarantine(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      group_name TEXT,
      source_id TEXT,
      reason TEXT NOT NULL,
      raw_json TEXT NOT NULL
    );
    """)
    db.executemany("INSERT OR IGNORE INTO factor_groups(group_name,description) VALUES (?,?)",GROUPS.items())
    db.commit()
    counts={table:db.execute("SELECT COUNT(*) FROM "+table).fetchone()[0] for table in
            ("fixtures","source_documents","factor_groups","observations","quarantine")}
    db.close()
    return counts

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("/tmp/matchlens_factors.sqlite")
    print(create(path))
