import unittest
from datetime import datetime, timezone
from scripts.restore_openfootball_history import completed_seasons

class RecentHistoryTests(unittest.TestCase):
    def test_october_uses_last_two_completed_seasons(self):
        self.assertEqual(completed_seasons(datetime(2026,10,31,tzinfo=timezone.utc)),
                         ("2024-25","2025-26"))
    def test_march_does_not_include_current_season(self):
        self.assertEqual(completed_seasons(datetime(2027,3,1,tzinfo=timezone.utc)),
                         ("2024-25","2025-26"))

if __name__=="__main__":
    unittest.main()
