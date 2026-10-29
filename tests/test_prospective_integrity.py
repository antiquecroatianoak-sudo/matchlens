import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analytics import prospective as p


class IntegrityTests(unittest.TestCase):
    def prediction(self, **values):
        return dict(key='en.1|2026-27|A|B', date='2026-10-30',
                    as_of='2026-10-29', generated_at='2026-10-29T06:00:00+00:00', **values)

    def test_timestamp_rules(self):
        base = self.prediction()
        self.assertIsNone(p.timing_rejection(base))
        self.assertIsNone(p.timing_rejection(base, {'date': '2026-11-01'}))
        for changed in (
            {'generated_at': '2026-10-30T00:00:00Z'},
            {'generated_at': '2026-10-31T00:00:00Z'},
            {'generated_at': '2026-10-29T06:00:00'},
            {'generated_at': 'bad'},
            {'as_of': '2026-10-30'},
            {'date': 'bad'},
        ):
            with self.subTest(changed=changed):
                self.assertIsNotNone(p.timing_rejection({**base, **changed}))
        self.assertIsNotNone(p.timing_rejection(base, {'date': '2026-10-29'}))
        self.assertIsNotNone(p.timing_rejection({**base, 'generated_at': '2026-10-30T00:30:00-02:00'}))
        self.assertIsNotNone(p.timing_rejection({k:v for k,v in base.items() if k != 'generated_at'}))

    def test_changed_code_and_backdating_fail_before_any_output(self):
        with tempfile.TemporaryDirectory() as folder:
            doc = {'lock_date': '2026-10-28', 'code_sha256': {'a': 'old'}}
            with patch.object(p, 'load_lock', return_value=(doc, {})), patch.object(p, 'code_hashes', return_value={'a': 'new'}):
                with self.assertRaisesRegex(ValueError, 'Code changed'):
                    p.predict(folder, folder, '2026-10-29', 7)
            doc['code_sha256'] = {'a': 'new'}
            with patch.object(p, 'load_lock', return_value=(doc, {})), patch.object(p, 'code_hashes', return_value={'a': 'new'}), patch.object(p, 'now', return_value='2026-10-29T06:00:00+00:00'):
                for as_of in ['2026-10-28', '2026-10-30']:
                    with self.assertRaisesRegex(ValueError, 'actual UTC'):
                        p.predict(folder, folder, as_of, 7)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_score_excludes_late_records_without_rewriting_log(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT) as folder:
            root = Path(folder)
            base = self.prediction()
            rows = [{**base, 'generated_at': '2026-10-30T12:00:00Z'},
                    {**base, 'key': 'pending', 'generated_at': 'bad'},
                    {**base, 'key': 'valid-pending'}]
            log = root / 'prospective-predictions.jsonl'
            original = ''.join(json.dumps(r)+'\n' for r in rows)
            log.write_text(original)
            result = dict(date='2026-10-30', league='en.1', season='2026-27', home='A', away='B', hg=1, ag=0)
            with patch.object(p, 'load_matches', return_value=([result], {})):
                report = p.score(folder, folder)
            self.assertEqual((report['scored'], report['pending'], report['excluded']), (0, 1, 2))
            self.assertFalse(report['enough_for_claims'])
            self.assertEqual(log.read_text(), original)


if __name__ == '__main__':
    unittest.main()
