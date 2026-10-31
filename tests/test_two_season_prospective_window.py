import unittest
from datetime import date
from scripts.score_future_baseline import last_two_completed_seasons


class TwoSeasonWindowTests(unittest.TestCase):
    def test_october_2026(self):
        self.assertEqual(last_two_completed_seasons(date(2026, 10, 31)), {'2024-25', '2025-26'})

    def test_before_july_rollover(self):
        self.assertEqual(last_two_completed_seasons(date(2027, 6, 30)), {'2024-25', '2025-26'})

    def test_after_july_rollover(self):
        self.assertEqual(last_two_completed_seasons(date(2027, 7, 1)), {'2025-26', '2026-27'})


if __name__ == '__main__':
    unittest.main()
