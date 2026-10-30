import unittest
from analytics.historical_baseline import walk_forward, probabilities

class HistoricalBaselineTests(unittest.TestCase):
    def test_probabilities(self):
        p = probabilities(1.4, 1.1)
        self.assertAlmostEqual(sum(p[:3]), 1, places=7)
        self.assertTrue(0 < p[3] < 1)

    def test_walk_forward_no_future_leakage(self):
        rows = [
            dict(match_id="a", kickoff="2025-01-01T12:00:00Z", home="A", away="B", home_goals=1, away_goals=0),
            dict(match_id="b", kickoff="2025-01-02T12:00:00Z", home="C", away="D", home_goals=8, away_goals=0),
            dict(match_id="c", kickoff="2025-01-03T12:00:00Z", home="E", away="F", home_goals=0, away_goals=1)]
        result = walk_forward(rows, min_history=1, delay_days=2)
        self.assertEqual(result["predictions"][0]["match_id"], "c")
        self.assertEqual(result["predictions"][0]["training_matches"], 1)

    def test_unknown_outcome_not_scored(self):
        rows = [
            dict(match_id="a", kickoff="2025-01-01T12:00:00Z", home="A", away="B", home_goals=1, away_goals=0),
            dict(match_id="b", kickoff="2025-01-04T12:00:00Z", home="A", away="B", home_goals=None, away_goals=None)]
        result = walk_forward(rows, min_history=1)
        self.assertEqual(len(result["predictions"]), 1)
        self.assertEqual(result["scored"], 0)

if __name__ == "__main__":
    unittest.main()
