import unittest
from scripts.select_prospective_model import combine

class ModelSelectionTests(unittest.TestCase):
    def test_advanced_overrides_baseline_for_same_fixture(self):
        base = [{"id":"openligadb:1","model":"historical_poisson_fallback_v1"}]
        advanced = [{"id":"openligadb:1","model":"factor_search_v1_two_completed_seasons"}]
        self.assertEqual(combine(base,advanced)[0]["model"],"factor_search_v1_two_completed_seasons")

    def test_baseline_is_explicit_fallback(self):
        base = [{"id":"openligadb:1","model":"historical_poisson_fallback_v1"}]
        self.assertEqual(combine(base,[]),base)

    def test_advanced_only_fixture_is_included(self):
        advanced = [{"id":"openligadb:2","model":"factor_search_v1_two_completed_seasons"}]
        self.assertEqual(combine([],advanced),advanced)

if __name__ == "__main__":
    unittest.main()
