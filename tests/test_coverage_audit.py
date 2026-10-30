import unittest
from analytics.coverage_audit import audit, REQUIRED, BOOKMAKER_MARKETS
from analytics.full_market_evaluation import MARKETS

class CoverageAuditTests(unittest.TestCase):
    def test_missing_not_imputed(self):
        result = audit([{"home_goals":1,"away_goals":0}])
        self.assertEqual(result["full_cohort"],0)
        self.assertEqual(set(result["missing_factors"]),set(REQUIRED))
        self.assertTrue(all(result["missing_odds"][m]==1 for m in BOOKMAKER_MARKETS))
    def test_complete(self):
        row = {"factors":{k:1 for k in REQUIRED},"odds":{m:{"price":2.5} for m in MARKETS}}
        self.assertEqual(audit([row])["full_cohort"],1)
if __name__=="__main__":
    unittest.main()
