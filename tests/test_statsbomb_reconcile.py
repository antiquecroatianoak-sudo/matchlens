import unittest
from analytics.statsbomb_reconcile import reconcile_statsbomb_matches

CANONICAL = [{"id": "c1", "date": "2024-04-06", "home": "home-a", "away": "away-b"}]
PROVIDER = {"match_id": 123, "match_date": "2024-04-06", "home_team": {"home_team_id": 10}, "away_team": {"away_team_id": 20}}
MAPPING = {10: "home-a", 20: "away-b"}


class StatsBombReconcileTests(unittest.TestCase):
    def test_exact_explicit_mapping(self):
        result = reconcile_statsbomb_matches([PROVIDER], CANONICAL, MAPPING)
        self.assertEqual(result["paired"], [{"provider_match_id": 123, "canonical_match_id": "c1", "date": "2024-04-06"}])

    def test_no_fuzzy_or_implicit_mapping(self):
        result = reconcile_statsbomb_matches([PROVIDER], CANONICAL, {10: "home-a"})
        self.assertEqual(result["quarantined"][0]["reason"], "unmapped_team")

    def test_duplicate_provider_rejected(self):
        result = reconcile_statsbomb_matches([PROVIDER, PROVIDER], CANONICAL, MAPPING)
        self.assertEqual(result["paired_count"], 1)
        self.assertEqual(result["quarantined"][0]["reason"], "duplicate_provider_match")

    def test_ambiguous_canonical_fixture_rejected(self):
        result = reconcile_statsbomb_matches([PROVIDER], CANONICAL + [dict(CANONICAL[0], id="c2")], MAPPING)
        self.assertEqual(result["paired_count"], 0)
        self.assertEqual(result["quarantined"][0]["reason"], "ambiguous_or_missing_fixture")


if __name__ == "__main__":
    unittest.main()
