import json
import tempfile
import unittest
from pathlib import Path
from analytics.factor_snapshot_import import read_factor_jsonl

ROW = {
    "match_id": "match-1", "factor": "injury_count", "value": 2,
    "source": "approved-example",
    "observed_at": "2026-10-29T08:00:00Z",
    "available_at": "2026-10-29T09:00:00Z",
    "prediction_at": "2026-10-29T10:00:00Z",
}


class FactorSnapshotImportTests(unittest.TestCase):
    def check(self, rows, approved=("approved-example",), as_of="2026-10-29T10:00:00Z"):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "factors.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            return read_factor_jsonl(path, approved_sources=set(approved), as_of=as_of)

    def test_accepts_verified_row(self):
        self.assertEqual(self.check([ROW])["accepted_count"], 1)

    def test_rejects_unapproved_source(self):
        result = self.check([ROW], approved=("different",))
        self.assertIn("source_not_approved", result["rejected"][0]["errors"])

    def test_rejects_later_prediction(self):
        result = self.check([ROW], as_of="2026-10-29T09:30:00Z")
        self.assertIn("after_as_of", result["rejected"][0]["errors"])

    def test_rejects_duplicate(self):
        result = self.check([ROW, ROW])
        self.assertEqual((result["accepted_count"], result["rejected_count"]), (1, 1))
        self.assertIn("duplicate_observation", result["rejected"][0]["errors"])

    def test_rejects_missing_value(self):
        result = self.check([dict(ROW, value=None)])
        self.assertIn("missing:value", result["rejected"][0]["errors"])

    def test_no_implicit_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "factors.jsonl"
            path.write_text(json.dumps(ROW), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_factor_jsonl(path, approved_sources=set(), as_of="2026-10-29T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
