import unittest
import numpy as np
from unittest.mock import patch
from analytics import market_specialists as m


class SpecialistTests(unittest.TestCase):
    def test_embargo_excludes_same_day_future_and_pending(self):
        records=[dict(match=dict(id=str(i),date=day,pending=pending)) for i,(day,pending) in enumerate([
            ('2024-01-01',False),('2024-01-02',False),('2024-01-03',False),
            ('2024-01-04',False),('2025-01-01',False),('2024-01-01',True)])]
        self.assertEqual([r['match']['id'] for r in m.training_rows(records,'2024-01-04')],['0'])

    def test_selection_is_per_market_and_ignores_audit(self):
        def trial(i,a,b):
            return dict(id=i,development={s:dict(outcome_log_loss=a,goals_log_loss=b) for s in m.DEV})
        trials=[trial(0,.9,.7),trial(1,1.,.6)]
        self.assertEqual(m.choose(trials,'outcome')['id'],0)
        self.assertEqual(m.choose(trials,'goals')['id'],1)
        for row in trials:
            row['audit']={'outcome_log_loss':100-row['id']*100}
        self.assertEqual(m.choose(trials,'outcome')['id'],0)

    def test_combined_markets_are_normalized(self):
        first=np.array([[.6,.1,.3,.8,.2]])
        second=np.array([[.3,.3,.4,.55,.45]])
        actual=m.combine(first,second)
        np.testing.assert_allclose(actual,[[.6,.1,.3,.55,.45]])
        self.assertAlmostEqual(actual[0,:3].sum(),1.)
        self.assertAlmostEqual(actual[0,3:].sum(),1.)

    def test_quarterly_refit_uses_only_released_results(self):
        rows=[dict(match=dict(id=str(i),date=day,season='2024-25')) for i,day in enumerate([
            '2024-07-01','2024-07-04','2024-10-01','2024-10-04'])]
        rows.insert(0,dict(match=dict(id='earlier',date='2023-07-01',season='2023-24')))
        calls=[]
        def fit(train,config,cutoff,half):
            calls.append((cutoff,[r['match']['date'] for r in train]))
            return {}
        with patch.object(m,'fit_recency',side_effect=fit), patch.object(m,'intensities',side_effect=lambda block,model:np.ones((len(block),2))):
            p,_,_=m.chronological_predictions(rows,'2024-25',dict(rho=0,temperature=1),dict(refit='quarter',half_life_days=365))
        self.assertEqual(calls,[('2024-07-01',['2023-07-01']),('2024-10-01',['2023-07-01','2024-07-01','2024-07-04'])])
        self.assertEqual(len(p),4)


if __name__=='__main__':
    unittest.main()
