import unittest
from analytics.factor_intake import accepted_factors, validate_factor

BASE = {"match_id":"a","factor":"injury_count","value":2,"source":"licensed-feed",
        "observed_at":"2026-10-30T10:00:00Z","available_at":"2026-10-30T11:00:00Z",
        "prediction_at":"2026-10-30T12:00:00Z"}

class FactorIntakeTests(unittest.TestCase):
    def test_valid_historical_input(self):
        self.assertEqual(validate_factor(BASE), [])
    def test_future_information_rejected(self):
        row = dict(BASE, available_at="2026-10-30T12:00:00Z")
        self.assertIn("not_available_before_prediction", validate_factor(row))
    def test_missing_value_not_zero_filled(self):
        row = dict(BASE, value=None)
        self.assertIn("missing:value", validate_factor(row))
    def test_missing_timezone_rejected(self):
        row = dict(BASE, observed_at="2026-10-30T10:00:00")
        self.assertIn("invalid_timestamp:observed_at", validate_factor(row))
    def test_batch_counts(self):
        result = accepted_factors([BASE, dict(BASE, source="")])
        self.assertEqual((len(result["accepted"]), len(result["rejected"])), (1,1))

if __name__ == "__main__":
    unittest.main()
