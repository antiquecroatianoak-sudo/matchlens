import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ingestion.import_matches import import_csv

class ImportTests(unittest.TestCase):
    def test_large_repeat_correction_and_bad_row(self):
        with tempfile.TemporaryDirectory() as folder:
            csv_path, db_path = Path(folder)/'synthetic.csv', Path(folder)/'isolated.db'
            fields = ['source_match_id','kickoff','competition','home','away','home_goals','away_goals']
            def write(score):
                with csv_path.open('w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(fields)
                    for i in range(12001):
                        writer.writerow([str(i),'2020-01-01T12:00:00Z','SYNTHETIC','A','B',score if i == 0 else 1,0])
                    writer.writerow(['bad','no-time','SYNTHETIC','A','B',-1,0])
            write(1)
            first = import_csv(csv_path, db_path, 'synthetic-test', 1000)
            self.assertEqual(first['inserted'], 12001)
            self.assertEqual(first['rejected'], 1)
            second = import_csv(csv_path, db_path, 'synthetic-test', 1000)
            self.assertEqual(second['unchanged'], 12001)
            write(2)
            third = import_csv(csv_path, db_path, 'synthetic-test', 1000)
            self.assertEqual(third['updated'], 1)
            with sqlite3.connect(db_path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM matches').fetchone()[0], 12001)
                self.assertEqual(db.execute('SELECT home_goals FROM matches WHERE source_match_id="0"').fetchone()[0], 2)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM import_runs').fetchone()[0], 3)

if __name__ == '__main__':
    unittest.main()
