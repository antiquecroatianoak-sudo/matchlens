"""Fast offline regression tests for supplemental fixture matching."""
import unittest
from scripts.reconcile_football_sources import canonical_team

class TeamAliasTests(unittest.TestCase):
    def test_case_accents_and_spacing(self):
        self.assertEqual(canonical_team('  PSG  '),canonical_team('Paris Saint-Germain'))
        self.assertEqual(canonical_team('Man United'),canonical_team('Manchester United'))
        self.assertEqual(canonical_team('Spurs'),canonical_team('Tottenham Hotspur'))
    def test_distinct_teams_do_not_collapse(self):
        self.assertNotEqual(canonical_team('Manchester United'),canonical_team('Manchester City'))
        self.assertNotEqual(canonical_team('Real Madrid'),canonical_team('Atletico Madrid'))
    def test_unknown_team_preserved(self):
        self.assertEqual(canonical_team('Unknown FC'), 'unknown fc')

from scripts.top25_single_pick import select

class SinglePickSelectionTests(unittest.TestCase):
    def fixture(self, n, i, probs):
        return {'id':f'match-{i}', 'league':'en.1', 'season':'2024-25',
                'round':'1', 'prob':probs, 'actual':{
                    'home':True,'draw':False,'away':False,
                    'over2.5':False,'under2.5':True}}

    def test_exactly_one_market_per_selected_fixture(self):
        rows=[]
        for i in range(8):
            p={'home':0.30,'draw':0.25,'away':0.45,'over2.5':0.35,'under2.5':0.65}
            if i==0:p={'home':0.80,'draw':0.10,'away':0.10,'over2.5':0.55,'under2.5':0.45}
            if i==1:p={'home':0.25,'draw':0.15,'away':0.60,'over2.5':0.10,'under2.5':0.90}
            rows.append(self.fixture(8,i,p))
        report=select(rows)
        picks=report['selected']
        self.assertEqual(len(picks),2)
        self.assertEqual(len({p['id'] for p in picks}),2)
        self.assertEqual({p['id']:p['market'] for p in picks},
                         {'match-0':'home','match-1':'under2.5'})
        self.assertEqual(report['summary']['hits'],2)

    def test_abstain_below_confidence_threshold(self):
        rows=[]
        for i in range(8):
            p={'home':0.55,'draw':0.20,'away':0.25,
               'over2.5':0.40,'under2.5':0.60}
            if i==0:p={'home':0.82,'draw':0.08,'away':0.10,
                       'over2.5':0.52,'under2.5':0.48}
            rows.append(self.fixture(8,i,p))
        report=select(rows,min_confidence=0.80)
        self.assertEqual(report['summary']['selected'],1)
        self.assertEqual(report['selected'][0]['market'],'home')
        self.assertEqual(report['selected'][0]['id'],'match-0')
        self.assertLessEqual(report['summary']['selected'],len(rows)//4)

    def test_at_most_quarter_and_no_double_counting(self):
        rows=[self.fixture(10,i,{'home':0.6,'draw':0.1,'away':0.3,
                    'over2.5':0.4,'under2.5':0.6}) for i in range(10)]
        report=select(rows)
        self.assertEqual(report['summary']['selected'],2)
        self.assertEqual(report['summary']['evaluated'],2)
        self.assertEqual(report['summary']['hits'],2)
        self.assertTrue(all(p['market'] in ('home','draw','away','over2.5','under2.5')
                            for p in report['selected']))

if __name__=='__main__':
    unittest.main()
