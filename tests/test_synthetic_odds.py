import unittest
from analytics.synthetic_odds import terms,quote
from analytics.double_chance import offers
from analytics.synthetic_odds_audit import build


class SyntheticOddsTests(unittest.TestCase):
    def test_equal_payout_and_total_stake(self):
        t=terms('1X',{'1':5.,'X':4.})
        self.assertAlmostEqual(t['odds'],20/9)
        self.assertAlmostEqual(sum(t['stake_fractions'].values()),1.)
        self.assertAlmostEqual(t['stake_fractions']['1']*5,t['odds'])
        self.assertAlmostEqual(t['stake_fractions']['X']*4,t['odds'])

    def test_boundary_and_invalid_inputs(self):
        self.assertEqual(terms('1X',{'1':3.,'X':6.})['odds'],2.)
        for p in ({'1':1.,'X':4.},{'1':float('nan'),'X':4.},{'1':4.}):
            with self.assertRaises(ValueError):terms('1X',p)

    def snapshot(self):return dict(match_id='m',source='test',bookmaker='same-book',timestamp='2026-10-29T10:00:00Z',snapshot_id='s',odds={'1':5.,'X':4.,'2':1.5})

    def test_provenance_and_no_forged_calculation(self):
        q=quote(self.snapshot(),'1X');r=offers('m',[.2,.3,.5],[q],'2026-10-29T11:00:00Z','2026-10-30T12:00:00Z')
        self.assertEqual(r[0]['oddsBasis'],'synthetic_1x2')
        self.assertEqual(r[0]['underlyingSnapshotId'],'s')
        q['odds']=9.
        self.assertEqual(offers('m',[.2,.3,.5],[q],'2026-10-29T11:00:00Z','2026-10-30T12:00:00Z'),[])

    def test_unknown_result_stays_in_benchmark_scope(self):
        row=dict(id='1',country='England',league='Premier League',pin_open_home='5',pin_open_draw='4',pin_open_away='1.5',kickoff_utc='2026-10-29T12:00:00Z',result='',void_reason='postponed')
        pool,valid,invalid,n=build([row]);self.assertEqual((valid,invalid,n),(1,0,1))
        self.assertEqual(len(pool),1);self.assertIsNone(pool[0]['actual'])

    def test_foreign_league_not_added_and_duplicates_rejected(self):
        row=dict(id='1',country='England',league='Premier League',pin_open_home='5',pin_open_draw='4',pin_open_away='1.5',kickoff_utc='2026-10-29T12:00:00Z',result='1',void_reason='')
        with self.assertRaises(ValueError):build([row,row])
        self.assertEqual(build([dict(row,league='Championship')])[3],0)


if __name__=='__main__':unittest.main()
