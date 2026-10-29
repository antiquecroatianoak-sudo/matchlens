import copy
from datetime import date,timedelta
import unittest
import numpy as np
from analytics import factor_search as f
from analytics.expanded_search import features


def history():
    rows=[]
    for i in range(240):
        day=(date(2020,1,1)+timedelta(days=i*3)).isoformat()
        rows.append(dict(id=str(i),date=day,season='2019-20',league='en.1',
            home='A' if i%2 else 'B',away='B' if i%2 else 'A',hg=i%4,ag=i%3,round=str(i)))
    return rows


class FactorSearchTests(unittest.TestCase):
    def test_new_factors_ignore_target_and_future_outcomes(self):
        rows=history();records=features(rows,50,15);target=records[-5]['match']['id']
        first=f.extra_factors(rows,records)[target]
        changed=copy.deepcopy(rows)
        day=next(r['date'] for r in rows if r['id']==target)
        for r in changed:
            if r['date']>=day: r['hg']=99;r['ag']=88
        second=f.extra_factors(changed,features(changed,50,15))[target]
        np.testing.assert_array_equal(first,second)
        self.assertEqual(len(first),46)
        self.assertTrue(np.isfinite(first).all())

    def test_pending_fixtures_do_not_change_new_histories(self):
        rows=history();end=date.fromisoformat(rows[-1]['date'])
        pending=[dict(id='p'+str(i),date=(end+timedelta(days=7*(i+1))).isoformat(),season='2019-20',league='en.1',home='A',away='B',hg=99,ag=99,round='x',pending=True) for i in range(3)]
        mixed=rows+pending;alone=rows+pending[-1:]
        a=f.extra_factors(alone,features(alone,50,15))['p2'];b=f.extra_factors(mixed,features(mixed,50,15))['p2']
        np.testing.assert_array_equal(a,b)

    def test_design_dimensions_and_embargo(self):
        rows=history();records=features(rows,50,15)
        self.assertEqual(f.build_design(rows,records).shape,(len(records),84))
        sample=[dict(match=dict(date=d,season=s)) for d,s in [('2022-06-27','2021-22'),('2022-06-29','2021-22'),('2022-07-01','2022-23'),('2023-01-01','2022-23'),('2024-01-01','2023-24')]]
        self.assertEqual(f.training_mask(sample,'2022-23').tolist(),[True,False,False,False,False])

    def test_calibration_is_coherent_and_selection_ignores_audit(self):
        p=f.probabilities(np.array([[.7,.2,.1]]),np.array([.8]),.85,1.3)
        np.testing.assert_allclose(p[:,:3].sum(axis=1),[1.])
        np.testing.assert_allclose(p[:,3:].sum(axis=1),[1.])
        trials=[dict(id=0,development=dict(outcome_log_loss=.9,goals_log_loss=.7),audit=999),
                dict(id=1,development=dict(outcome_log_loss=1.,goals_log_loss=.6),audit=0)]
        self.assertEqual(f.choose(trials,'outcome')['id'],0)
        self.assertEqual(f.choose(trials,'goals')['id'],1)

    def test_no_random_holdout(self):
        self.assertFalse(f.learner(dict(leaves=7,l2=10)).early_stopping)


if __name__=='__main__': unittest.main()
