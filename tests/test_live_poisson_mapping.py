import unittest
from scripts.score_future_baseline import LEAGUE_MAP

class LeagueMappingTests(unittest.TestCase):
    def test_bundesliga_one_maps_to_historical_germany(self):
        self.assertEqual(LEAGUE_MAP['bl1'],'de.1')
    def test_bundesliga_two_is_not_misrepresented_as_first_division(self):
        self.assertNotIn('bl2',LEAGUE_MAP)

if __name__=='__main__':unittest.main()
