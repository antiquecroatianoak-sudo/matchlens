import unittest
from analytics.context_features import context_features

CUTOFF = "2025-10-01T12:00:00Z"
KICKOFF = "2025-10-01T18:00:00Z"

class ContextFeatureTests(unittest.TestCase):
    def test_valid_forecast(self):
        row = dict(kind="weather_forecast", source_id="weather-1", issued_at="2025-10-01T09:00:00Z", available_at="2025-10-01T10:00:00Z", temperature_c=13, precipitation_mm=2.5, wind_kmh=18, humidity_pct=70)
        result = context_features(row, CUTOFF, KICKOFF)
        self.assertEqual(result["features"]["temperature_c"], 13)
        self.assertIsNone(result["features"].get("surface"))

    def test_late_forecast_rejected(self):
        row = dict(kind="weather_forecast", source_id="weather-1", issued_at="2025-10-01T13:00:00Z", available_at="2025-10-01T13:01:00Z")
        self.assertIsNone(context_features(row, CUTOFF, KICKOFF))

    def test_pitch_report(self):
        row = dict(kind="pitch_report", source_id="stadium-1", issued_at="2025-10-01T09:00:00Z", available_at="2025-10-01T10:00:00Z", surface="natural_grass", wetness="wet")
        self.assertEqual(context_features(row, CUTOFF, KICKOFF)["features"]["wetness"], "wet")

    def test_missing_record_is_not_zero(self):
        self.assertIsNone(context_features(None, CUTOFF, KICKOFF))

    def test_invalid_cutoff(self):
        with self.assertRaises(ValueError):
            context_features({}, KICKOFF, KICKOFF)

    def test_invalid_humidity(self):
        row = dict(kind="weather_forecast", source_id="weather-1", issued_at="2025-10-01T09:00:00Z", available_at="2025-10-01T10:00:00Z", humidity_pct=130)
        with self.assertRaises(ValueError):
            context_features(row, CUTOFF, KICKOFF)

if __name__ == "__main__":
    unittest.main()
