import unittest
from scripts.score_future_baseline import normalize_team

class BundesligaAliasTests(unittest.TestCase):
    def test_known_bayern(self):
        self.assertEqual(normalize_team("FC Bayern München",{"Bayern München","Dortmund"}),"Bayern München")
    def test_unknown_fails_closed(self):
        self.assertIsNone(normalize_team("Unlisted Team",{"Bayern München"}))
    def test_exact_match(self):
        self.assertEqual(normalize_team("Borussia Dortmund",{"Borussia Dortmund"}),"Borussia Dortmund")
if __name__=="__main__":unittest.main()
