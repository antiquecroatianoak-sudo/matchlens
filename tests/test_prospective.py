import unittest
from datetime import date, timedelta
from analytics.expanded_search import features


def rows():
    out = []
    for i in range(220):
        day = (date(2020, 1, 1) + timedelta(days=i * 3)).isoformat()
        out.append(dict(id=str(i), date=day, season='2019-20', league='en.1', home='A' if i % 2 else 'B',
                        away='B' if i % 2 else 'A', hg=i % 4, ag=i % 3, round=str(i)))
    return out


class ProspectiveTests(unittest.TestCase):
    def test_pending_fixtures_never_enter_history(self):
        played = rows()
        last = date.fromisoformat(played[-1]['date'])
        pending = [dict(id='p%d' % k, date=(last + timedelta(days=5 + 7 * k)).isoformat(), season='2019-20', league='en.1',
                        home='A', away='B', hg=0, ag=0, round='x', pending=True) for k in range(3)]
        alone = {r['match']['id']: r for r in features(played + pending[-1:], 20, 15)}
        together = {r['match']['id']: r for r in features(played + pending, 20, 15)}
        self.assertEqual(alone['p2']['x'], together['p2']['x'])
        self.assertEqual(together['p2']['history_end'], played[-1]['date'])
        # A pending row with an extreme placeholder score changes nothing either.
        loud = [{**p, 'hg': 9, 'ag': 9} for p in pending]
        self.assertEqual(together['p2']['x'], {r['match']['id']: r for r in features(played + loud, 20, 15)}['p2']['x'])

    def test_played_rows_unchanged_by_pending_rows(self):
        played = rows()
        pending = [dict(id='p', date='2030-01-01', season='2019-20', league='en.1', home='A', away='B', hg=0, ag=0, round='x', pending=True)]
        base = {r['match']['id']: r['x'] for r in features(played, 20, 15)}
        mixed = {r['match']['id']: r['x'] for r in features(played + pending, 20, 15) if r['match']['id'] != 'p'}
        self.assertEqual(base, mixed)


if __name__ == '__main__':
    unittest.main()
