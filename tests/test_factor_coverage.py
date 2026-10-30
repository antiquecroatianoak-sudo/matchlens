import json
import tempfile
import unittest
from pathlib import Path
from analytics.factor_coverage import coverage_report

ROW = {
    "match_id": "a", "factor": "injury_count", "value": 1,
    "source": "approved", "observed_at": "2026-10-29T08:00:00Z",
    "available_at": "2026-10-29T09:00:00Z",
    "prediction_at": "2026-10-29T10:00:00Z",
}


class FactorCoverageTests(unittest.TestCase):
    def test_denominator_includes_missing_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "factors.jsonl"
            path.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
            report = coverage_report(
                path, approved_sources={"approved"},
                as_of="2026-10-29T10:00:00Z", expected_match_ids=["a", "b", "c", "d"]
            )
            self.assertEqual(report["expected_matches"], 4)
            self.assertEqual(report["factor_coverage"]["injury_count"]["fraction"], 0.25)

    def test_empty_expected_denominator_rejected(self):
        with self.assertRaises(ValueError):
            coverage_report("unused", approved_sources={"approved"}, as_of="2026-10-29T10:00:00Z", expected_match_ids=[])


if __name__ == "__main__":
    unittest.main()
