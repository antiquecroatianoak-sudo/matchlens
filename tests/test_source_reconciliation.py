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

if __name__=='__main__':
    unittest.main()
