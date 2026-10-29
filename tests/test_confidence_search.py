import copy
import unittest
import numpy as np
from analytics.confidence_search import (fit_calibration,apply_calibration,select_calibrator,
    pick_pool,select_gate,gate_report,choose_gate,history_quality,lower_bound,CONFIGS,RULES)


class ConfidenceTests(unittest.TestCase):
    def test_identity_and_unseen_league_are_valid_probabilities(self):
        p=np.array([[.6,.2,.2],[.2,.4,.4]]*110);y=np.array([0,2]*110)
        identity=fit_calibration(p,y,['en.1']*220,CONFIGS[0])
        np.testing.assert_array_equal(apply_calibration(p,['en.1']*220,identity),p)
        model=fit_calibration(p,y,['en.1']*220,dict(id='league',local=True,ridge=.1))
        corrected=apply_calibration(p,['unknown']*220,model)
        self.assertTrue(np.isfinite(corrected).all())
        self.assertTrue((corrected>0).all())
        np.testing.assert_allclose(corrected.sum(axis=1),1.)
        self.assertEqual(model['supported'],['en.1'])

    def test_selection_only_reads_development_metric(self):
        trials=[dict(config={'id':'a'},development_log_loss=.6,audit_accuracy=1.),
                dict(config={'id':'b'},development_log_loss=.5,audit_accuracy=0.)]
        self.assertEqual(select_calibrator(trials)['config']['id'],'b')

    def test_gate_preserves_unknowns_and_selection_ignores_outcomes(self):
        pool=[dict(id=str(i),match_id=str(i),date='2025-01-01',prob=.95,
                   agrees=True,min_history=30,max_recorded_gap=7,actual=None if i==0 else 0) for i in range(4)]
        rule=dict(profile='history_agree',threshold=.9,id='test')
        self.assertEqual(len(select_gate(pool,rule)),4)
        changed=copy.deepcopy(pool)
        for r in changed:r['actual']=1
        self.assertEqual([r['id'] for r in select_gate(pool,rule)],[r['id'] for r in select_gate(changed,rule)])
        report=gate_report(pool,rule)
        self.assertEqual((report['selected'],report['scored'],report['unscored']),(4,3,1))
        self.assertEqual(report['misses'],3)

    def test_history_embargo_and_pending(self):
        def row(mid,day,pending=False):
            return dict(id=mid,date=day,league='en.1',home='A',away='B',pending=pending)
        rows=[row('old','2023-01-01'),row('pending','2023-01-03',True),
              row('embargo','2023-01-08'),row('target','2023-01-10')]
        q=history_quality(rows)['target']
        self.assertEqual(q,dict(min_history=1,max_recorded_gap=9))

    def test_no_90_gate_without_sample_and_lower_bound(self):
        self.assertLess(lower_bound(13,13,len(RULES)),.9)
        self.assertLess(lower_bound(180,200,len(RULES)),.9)
        self.assertIsNone(choose_gate([dict(development_90_screen=False,rule={'id':'a'})]))

    def test_pick_pool_has_one_offer_per_fixture(self):
        m=dict(id='m',league='en.1',season='2025-26',date='2025-01-01',hg=0,ag=0,pending=True)
        p=np.array([[.8,.1,.1,.9,.1]])
        pool=pick_pool([dict(match=m)],p,p,{'m':dict(min_history=30,max_recorded_gap=7)})
        self.assertEqual(len(pool),1)
        self.assertIsNone(pool[0]['actual'])
        self.assertAlmostEqual(pool[0]['prob'],.9)
        self.assertEqual(len(RULES),28)


if __name__=='__main__':
    unittest.main()
