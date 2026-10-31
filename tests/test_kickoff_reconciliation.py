import unittest
from scripts.kickoff_reconciliation import reconcile_kickoffs


class KickoffReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = dict(competition="Premier League", home="A", away="B")

    def test_two_independent_sources_agree(self):
        rows = [dict(self.fixture, source="one", kickoff_iso="2026-10-31T15:00:00Z"),
                dict(self.fixture, source="two", kickoff_iso="2026-10-31T16:00:00+01:00")]
        result = reconcile_kickoffs(rows)
        self.assertEqual(len(result["accepted"]), 1)
        self.assertEqual(result["accepted"][0]["kickoff_utc"], "2026-10-31T15:00:00+00:00")

    def test_naive_time_is_rejected(self):
        result = reconcile_kickoffs([dict(self.fixture, source="one", kickoff_iso="2026-10-31T15:00:00")])
        self.assertFalse(result["accepted"])
        self.assertTrue(result["rejected"])

    def test_conflicting_sources_are_rejected(self):
        rows = [dict(self.fixture, source="one", kickoff_iso="2026-10-31T15:00:00Z"),
                dict(self.fixture, source="two", kickoff_iso="2026-10-31T16:00:00Z")]
        self.assertFalse(reconcile_kickoffs(rows)["accepted"])

    def test_duplicate_same_source_not_independent(self):
        row = dict(self.fixture, source="one", kickoff_iso="2026-10-31T15:00:00Z")
        self.assertFalse(reconcile_kickoffs([row, row])["accepted"])


if __name__ == "__main__":
    unittest.main()
