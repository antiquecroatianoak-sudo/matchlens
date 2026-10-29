import copy
import unittest
from datetime import date, timedelta
from pathlib import Path
from analytics.wyscout_pilot import build_features, normalize, GROUPS, BASE, partition


class WyscoutPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        for week in range(100):
            for pair in range(10):
                home, away = pair*2+1, pair*2+2
                if week % 2:
                    home, away = away, home
                def side(team):
                    return dict(team=team, coach=team+100,
                                lineup=[team*100+p for p in range(11)], score=(week+team)%4)
                cls.rows.append(dict(id=f'test:{week}:{pair}', league='England',
                                     date=(date(2017, 1, 1)+timedelta(days=week*7)).isoformat(),
                                     home=side(home), away=side(away)))
        cls.records = build_features(cls.rows)

    def test_real_coverage_and_unique_ids(self):
        if not Path('data/wyscout/raw/matches_England.json').exists():
            self.skipTest('Optional attributed raw source snapshot not downloaded')
        rows = normalize('data/wyscout/raw')
        self.assertEqual(len(rows), 1826)
        self.assertEqual(len({r['id'] for r in rows}), 1826)
        for r in rows:
            for side in ('home', 'away'):
                self.assertEqual(set(r[side]), {'team', 'coach', 'lineup', 'score'})
                self.assertEqual(len(set(r[side]['lineup'])), 11)

    def test_target_and_future_outcomes_do_not_change_current_features(self):
        target = self.records[700]
        mutated = copy.deepcopy(self.rows)
        for r in mutated:
            if r['date'] >= target['date']:
                r['home']['score'] = 9
                r['away']['score'] = 8
        changed = {r['id']:r for r in build_features(mutated)}
        for r in self.records:
            if r['date'] <= target['date']:
                self.assertEqual(r['x'], changed[r['id']]['x'])

    def test_two_day_history_embargo(self):
        target = self.records[700]
        from datetime import date, timedelta
        embargo = (date.fromisoformat(target['date'])-timedelta(days=2)).isoformat()
        mutated = copy.deepcopy(self.rows)
        for r in mutated:
            if embargo <= r['date'] <= target['date']:
                r['home']['score'] = 9
                r['away']['score'] = 8
        changed = {r['id']:r for r in build_features(mutated)}
        self.assertEqual(target['x'], changed[target['id']]['x'])

    def test_missing_coach_is_explicit(self):
        rows = copy.deepcopy(self.rows)
        target_id = self.records[700]['id']
        for r in rows:
            if r['id'] == target_id:
                r['home']['coach'] = None
        target = next(r for r in build_features(rows) if r['id']==target_id)
        self.assertEqual(target['x'][18], 1.)
        self.assertEqual(target['x'][15], 0.)

    def test_ablation_columns_and_chronology(self):
        self.assertFalse(set(BASE) & set(GROUPS['both']))
        self.assertEqual(set(GROUPS['both']), set(GROUPS['coach']) | set(GROUPS['players']))
        self.assertEqual(set(BASE+GROUPS['both']), set(range(29)))
        train, dev, audit = partition(self.records)
        self.assertLess(max(r['date'] for r in train), min(r['date'] for r in dev))
        self.assertLess(max(r['date'] for r in dev), min(r['date'] for r in audit))


if __name__ == '__main__':
    unittest.main()
