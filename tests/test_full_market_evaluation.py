import unittest
from analytics.full_market_evaluation import evaluate

def row():
    return {"prediction_at":"2025-01-01T10:00:00Z","kickoff":"2025-01-01T20:00:00Z",
      "home_goals":2,"away_goals":1,"factors":{"weather":1,"lineup":1},
      "probabilities":{"1":.5,"X":.3,"2":.2,"over_2_5":.6},
      "odds":{m:{"price":p,"available_at":"2025-01-01T09:00:00Z"}
              for m,p in {"1":2.1,"X":3.2,"2":4.0,"over_2_5":2.1,"under_2_5":1.8,"1X":2.05,"X2":2.2}.items()}}
class FullMarketTests(unittest.TestCase):
    def test_all_markets(self):
        v=evaluate([row()],("weather","lineup"))["markets"]
        self.assertEqual(len(v),7)
        self.assertEqual(v["1X"]["eligible"],0)
        self.assertEqual(v["X2"]["eligible"],0)
    def test_late_quote_excluded(self):
        r=row();r["odds"]["1X"]["available_at"]="2025-01-01T12:00:00Z"
        self.assertEqual(evaluate([r])["markets"]["1X"]["eligible"],0)
    def test_missing_factor_excluded(self):
        self.assertEqual(evaluate([row()],("injury",))["markets"]["1"]["eligible"],0)
    def test_double_chance_price_threshold(self):
        r=row();r["odds"]["1X"]["price"]=2.
        self.assertEqual(evaluate([r])["markets"]["1X"]["eligible"],0)
if __name__=="__main__":
    unittest.main()

    def test_synthetic_1x_above_two(self):
        r=row();r["probabilities"]={"1":.15,"X":.25,"2":.60,"over_2_5":.6}
        x=evaluate([r])["markets"]["1X"]
        self.assertEqual(x["eligible"],1)
        self.assertIsNone(x["profit_units"])
