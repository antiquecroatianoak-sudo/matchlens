"""Regression checks for verified fixture-to-history team mapping (no network)."""
import unittest

from scripts.score_future_baseline import normalize_team


class HistoricalTeamMappingTests(unittest.TestCase):
    def test_openliga_alias_matches_historical_name(self):
        known = {"Bayern München", "Borussia Dortmund"}
        self.assertEqual(normalize_team("FC Bayern München", known), "Bayern München")

    def test_unicode_and_punctuation_normalization(self):
        self.assertEqual(normalize_team("Borussia Monchengladbach", {"Borussia Mönchengladbach"}), "Borussia Mönchengladbach")

    def test_hoffenheim_short_alias(self):
        self.assertEqual(normalize_team("TSG Hoffenheim", {"Hoffenheim"}), "Hoffenheim")

    def test_unknown_team_fails_closed(self):
        self.assertIsNone(normalize_team("Invented FC", {"Bayern München"}))

    def test_ambiguous_normalization_fails_closed(self):
        self.assertIsNone(normalize_team("A-B", {"A B", "AB"}))


if __name__ == "__main__":
    unittest.main()
