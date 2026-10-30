import unittest
from analytics.factor_assembly import assemble
class AssemblyTests(unittest.TestCase):
    def test_future_data_rejected(self):
        m={"match_id":"a","kickoff":"2025-01-03T20:00:00Z","feature_records":{"weather":[{"value":12,"source_id":"forecast","available_at":"2025-01-03T15:00:00Z"}]}}
        x=assemble(m,"2025-01-03T10:00:00Z",("weather",))
        self.assertFalse(x["complete"])
    def test_prior_record_selected(self):
        m={"match_id":"a","kickoff":"2025-01-03T20:00:00Z","feature_records":{"weather":[{"value":8,"source_id":"forecast","available_at":"2025-01-02T10:00:00Z"},{"value":12,"source_id":"forecast","available_at":"2025-01-03T15:00:00Z"}]}}
        x=assemble(m,"2025-01-03T10:00:00Z",("weather",))
        self.assertEqual(x["features"]["weather"]["value"],8)
    def test_after_kickoff_invalid(self):
        with self.assertRaises(ValueError):
            assemble({"match_id":"a","kickoff":"2025-01-03T20:00:00Z"},"2025-01-03T20:00:00Z",())
if __name__=="__main__": unittest.main()
