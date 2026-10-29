import copy,unittest
from datetime import date,timedelta
import numpy as np
from analytics.round_quarter import frozen_features,select_round
from analytics.expanded_search import features


class RoundQuarterTests(unittest.TestCase):
    def rows(self):
        rows=[dict(id=str(i),date=(date(2023,1,1)+timedelta(days=i)).isoformat(),league='en.1',season='2022-23',round=str(i),home='A',away='B',hg=i%3,ag=i%2) for i in range(120)]
        targets=[dict(rows[-1],id='friday',date='2023-05-12',round='new',hg=3,ag=0),dict(rows[-1],id='sunday',date='2023-05-14',round='new',hg=0,ag=2)]
        return rows+targets,targets

    def test_no_earlier_round_result_leaks_into_later_fixture(self):
        rows,targets=self.rows();a=frozen_features(rows,targets,'2023-05-12',50,15)
        changed=copy.deepcopy(rows);changed[-2]['hg']=9;changed[-2]['ag']=8
        b=frozen_features(changed,changed[-2:],'2023-05-12',50,15)
        for x,y in zip(a,b):np.testing.assert_array_equal(x['x'],y['x'])
        self.assertTrue(all(r['history_end']<'2023-05-10' for r in a))

    def test_matches_original_features_at_same_first_fixture_cutoff(self):
        rows,targets=self.rows();a=frozen_features(rows,targets[:1],'2023-05-12',50,15)[0]
        b=next(r for r in features(rows,50,15) if r['match']['id']=='friday')
        np.testing.assert_allclose(a['x'],b['x'],rtol=0,atol=1e-12)

    def test_selection_never_uses_outcomes_and_counts_unknowns(self):
        pool=[dict(match_id=str(i),prob=.9-i*.01,margin=.2,actual=None if i==0 else 0) for i in range(8)]
        selected=select_round(pool,8,0)
        self.assertIsNone(selected[0]['actual']);self.assertEqual(len(selected),2)
        changed=[dict(r,actual=1) for r in pool]
        self.assertEqual([r['match_id'] for r in selected],[r['match_id'] for r in select_round(changed,8,0)])

    def test_whole_round_budget_even_if_prediction_missing(self):
        pool=[dict(match_id=str(i),prob=.8,margin=.1,actual=1) for i in range(3)]
        self.assertEqual(len(select_round(pool,10,0)),2)
        self.assertEqual(len(select_round(pool,3,0)),0)

    def test_duplicate_fixture_rejected(self):
        r=dict(match_id='same',prob=.9,margin=.1,actual=1)
        with self.assertRaises(ValueError):select_round([r,r],8,0)


if __name__=='__main__':unittest.main()
