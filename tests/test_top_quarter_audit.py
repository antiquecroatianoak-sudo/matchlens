"""Unit checks for confidence ranking and scoring (no historical data needed)."""
import unittest
from analytics.top_quarter_audit import pick, summarize

class TopQuarterTests(unittest.TestCase):
    def test_strongest_market_and_hit(self):
        row = {"id":"m1","date":"2025-01-01","season":"2024-25","league":"en.1",
               "prob":{"home":.2,"draw":.1,"away":.7,"over2.5":.6,"under2.5":.4},
               "actual":{"home":0,"draw":0,"away":1,"over2.5":0,"under2.5":1}}
        p = pick(row)
        self.assertEqual((p["market"],p["hit"],p["confidence"]),("away",1,.7))
    def test_summary_counts(self):
        rows=[{"hit":1,"confidence":.8},{"hit":0,"confidence":.6}]
        result=summarize(rows)
        self.assertEqual((result["selected"],result["hits"],result["misses"]),(2,1,1))
        self.assertEqual(result["accuracy"],.5)
    def test_empty(self):
        self.assertIsNone(summarize([])["accuracy"])

if __name__ == "__main__":
    unittest.main()
