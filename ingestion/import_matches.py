"""Streaming CSV import into an isolated MatchLens SQLite database.

Canonical CSV: source_match_id,kickoff,competition,home,away,home_goals,away_goals
Optional: published_at. kickoff and published_at require explicit timezone offsets.
"""
import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = {'source_match_id', 'kickoff', 'competition', 'home', 'away', 'home_goals', 'away_goals'}


def timestamp(value):
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    return date.astimezone(timezone.utc).isoformat()


def import_csv(csv_path, db_path, source, batch_size=1000):
    if not source.strip() or batch_size < 1:
        raise ValueError('Source and positive batch size required')
    if Path(csv_path).resolve() == Path(db_path).resolve():
        raise ValueError('Input and database paths must differ')
    stats = dict(read=0, inserted=0, updated=0, unchanged=0, rejected=0)
    with sqlite3.connect(db_path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS matches (
            source TEXT NOT NULL, source_match_id TEXT NOT NULL,
            kickoff TEXT NOT NULL, competition TEXT NOT NULL,
            home TEXT NOT NULL, away TEXT NOT NULL,
            home_goals INTEGER NOT NULL, away_goals INTEGER NOT NULL,
            published_at TEXT, observed_at TEXT NOT NULL,
            payload_hash TEXT NOT NULL, raw_json TEXT NOT NULL,
            PRIMARY KEY(source, source_match_id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS import_runs (
            started_at TEXT, finished_at TEXT, source TEXT, summary TEXT)''')
        db.commit()
        started = datetime.now(timezone.utc).isoformat()
        with open(csv_path, encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError('Missing CSV fields: ' + ', '.join(sorted(REQUIRED - set(reader.fieldnames or []))))
            for row in reader:
                stats['read'] += 1
                try:
                    clean = {key: (row[key] or '').strip() for key in REQUIRED}
                    if not all(clean.values()):
                        raise ValueError('Empty required field')
                    clean['kickoff'] = timestamp(clean['kickoff'])
                    for key in ('home_goals', 'away_goals'):
                        clean[key] = int(clean[key])
                        if clean[key] < 0:
                            raise ValueError('Negative score')
                    if clean['home'] == clean['away']:
                        raise ValueError('Identical teams')
                    clean['published_at'] = timestamp(row['published_at']) if row.get('published_at') else None
                    raw = json.dumps(row, ensure_ascii=False, sort_keys=True)
                    digest = hashlib.sha256(raw.encode()).hexdigest()
                    previous = db.execute('SELECT payload_hash FROM matches WHERE source=? AND source_match_id=?', (source, clean['source_match_id'])).fetchone()
                    if previous and previous[0] == digest:
                        stats['unchanged'] += 1
                    else:
                        db.execute('''INSERT INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                            ON CONFLICT(source,source_match_id) DO UPDATE SET
                            kickoff=excluded.kickoff, competition=excluded.competition,
                            home=excluded.home, away=excluded.away,
                            home_goals=excluded.home_goals, away_goals=excluded.away_goals,
                            published_at=excluded.published_at, observed_at=excluded.observed_at,
                            payload_hash=excluded.payload_hash, raw_json=excluded.raw_json''',
                            (source, clean['source_match_id'], clean['kickoff'], clean['competition'], clean['home'], clean['away'], clean['home_goals'], clean['away_goals'], clean['published_at'], datetime.now(timezone.utc).isoformat(), digest, raw))
                        stats['updated' if previous else 'inserted'] += 1
                except (ValueError, TypeError, KeyError):
                    stats['rejected'] += 1
                if stats['read'] % batch_size == 0:
                    db.commit()
        db.execute('INSERT INTO import_runs VALUES (?,?,?,?)', (started, datetime.now(timezone.utc).isoformat(), source, json.dumps(stats)))
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv')
    parser.add_argument('--database', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--batch-size', type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(import_csv(args.csv, args.database, args.source, args.batch_size)))
