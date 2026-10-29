import copy,unittest
from analytics.criteria_audit import prior_criteria,accepts,choose_exclusion,RULES
from analytics.backtest import LEAGUES


class CriteriaTests(unittest.TestCase):
    def rows(self):
        return [dict(id=str(i),date=f'2023-01-{i*3+1:02}',league='en.1',season='2022-23',home='A',away='B',hg=2,ag=0) for i in range(8)]

    def test_target_outcome_never_enters_criteria(self):
        rows=self.rows();original=prior_criteria(rows);changed=copy.deepcopy(rows)
        changed[-1]['hg']=0;changed[-1]['ag']=9
        self.assertEqual(original[rows[-1]['id']],prior_criteria(changed)[rows[-1]['id']])

    def test_pending_results_and_embargo_excluded(self):
        rows=self.rows();rows[0]['pending']=True
        target=dict(rows[-1],id='target',date='2023-01-24')
        rows.append(target);c=prior_criteria(rows)['target']
        self.assertEqual(c['home']['n10'],6)
        # Same-day or two-day-old result cannot enter.
        rows.insert(-1,dict(rows[-2],id='too-recent',date='2023-01-23',hg=9,ag=0))
        self.assertEqual(c,prior_criteria(rows)['target'])

    def test_streak_and_venue_and_h2h_have_support(self):
        rows=self.rows();c=prior_criteria(rows)[rows[-1]['id']]
        self.assertEqual(c['home']['streak'],dict(result=1,length=7))
        self.assertEqual(c['home']['venue_gf'],2)
        self.assertEqual(c['away']['venue_gf'],0)
        self.assertEqual(c['h2h_n'],5)

    def test_missing_history_does_not_pass(self):
        c=prior_criteria(self.rows())['0']
        row=dict(prob=.9,col=0,criteria=c)
        for profile in ('form5','form10','venue10','streak2','h2h3'):
            self.assertFalse(accepts(row,dict(profile=profile,threshold=.8)))
        self.assertEqual(len(RULES),18)

    def test_exclusion_requires_two_supported_bad_seasons(self):
        dev={s:{code:dict(matches=200,deficit=0.) for code in LEAGUES} for s in ('2022-23','2023-24')}
        dev['2023-24']['be.1']['deficit']=.1
        self.assertIsNone(choose_exclusion(dev))
        dev['2022-23']['be.1']['deficit']=.08
        self.assertEqual(choose_exclusion(dev),'be.1')
        dev['2022-23']['be.1']['matches']=0
        self.assertIsNone(choose_exclusion(dev))


if __name__=='__main__':unittest.main()
