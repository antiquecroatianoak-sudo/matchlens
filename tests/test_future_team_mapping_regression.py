"""Regression checks for verified fixture-to-history team mapping (no network)."""
import unittest

from scripts.score_future_baseline import normalize_team
from analytics.backtest import load_matches
import json
import tempfile
from pathlib import Path


class HistoricalTeamMappingTests(unittest.TestCase):
    def test_openliga_alias_matches_historical_name(self):
        known = {"Bayern München", "Borussia Dortmund"}
        self.assertEqual(normalize_team("FC Bayern München", known), "Bayern München")

    def test_unicode_and_punctuation_normalization(self):
        self.assertEqual(normalize_team("Borussia Monchengladbach", {"Borussia Mönchengladbach"}), "Borussia Mönchengladbach")

    def test_hoffenheim_short_alias(self):
        self.assertEqual(normalize_team("TSG Hoffenheim", {"Hoffenheim"}), "Hoffenheim")

    def test_second_division_history_is_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "2024-25.de.2.json").write_text(json.dumps({
                "matches": [{"date": "2025-01-01", "team1": "Team A",
                             "team2": "Team B", "score": {"ft": [2, 1]}}]
            }))
            default_rows, _ = load_matches(folder)
            opt_in_rows, _ = load_matches(folder, extra_leagues=("de.2",))
            self.assertEqual(default_rows, [])
            self.assertEqual(len(opt_in_rows), 1)
            self.assertEqual(opt_in_rows[0]["league"], "de.2")

    def test_unknown_team_fails_closed(self):
        self.assertIsNone(normalize_team("Invented FC", {"Bayern München"}))

    def test_ambiguous_normalization_fails_closed(self):
        self.assertIsNone(normalize_team("A-B", {"A B", "AB"}))


if __name__ == "__main__":
    unittest.main()
