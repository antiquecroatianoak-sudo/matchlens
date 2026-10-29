import unittest
import numpy as np
from analytics.joint_quarter import choose_offer,earliest_bound,norm
from analytics.round_quarter import select_round


class JointQuarterTests(unittest.TestCase):
    def match(self,**kw):return dict(dict(id='m',date='2026-08-28',league='de.1',season='2026-27',round='r1',hg=1,ag=1),**kw)

    def test_one_joint_choice_across_seven_markets(self):
        p=np.array([.1,.2,.7,.6,.4]);q=dict(prices={'1':1.3,'X':5.,'2':5.})
        r=choose_offer(self.match(),p,q)
        self.assertEqual(r['market'],'X2');self.assertAlmostEqual(r['prob'],.9)
        self.assertEqual(r['synthetic_odds'],2.5);self.assertEqual(r['actual'],1)

    def test_missing_or_subtwo_price_does_not_invent_double_chance(self):
        p=np.array([.1,.2,.7,.6,.4])
        self.assertEqual(choose_offer(self.match(),p)['market'],'away')
        self.assertEqual(choose_offer(self.match(),p,dict(prices={'1':1.3,'X':2.,'2':2.}))['market'],'away')

    def test_outcome_does_not_change_market_or_fixture_choice(self):
        p=np.array([.1,.2,.7,.6,.4]);q=dict(prices={'1':1.3,'X':5.,'2':5.})
        a=choose_offer(self.match(),p,q);b=choose_offer(self.match(hg=9,ag=0),p,q)
        self.assertEqual((a['market'],a['prob']),(b['market'],b['prob']))
        self.assertEqual(len(select_round([a],8,0)),1)

    def test_conservative_round_bound_and_exact_name_normalization(self):
        m=self.match();self.assertEqual(earliest_bound([m],{'m':'20:30'}).isoformat(),'2026-08-28T17:30:00+00:00')
        self.assertEqual(norm('FC Bayern München'),norm('Bayern München'))
        self.assertNotEqual(norm('Manchester United FC'),norm('Manchester City FC'))


if __name__=='__main__':unittest.main()
