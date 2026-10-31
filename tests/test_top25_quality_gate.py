import unittest
from scripts.top25_quality_gate import assess, REQUIRED_EVIDENCE

class GateTests(unittest.TestCase):
    def setUp(self):
        self.backtest={"status":"research_only","final_test":{"matches":100}}
        self.top25={"status":"research_only","selected_observed_top_quarter":20,"hits":15}

    def test_missing_evidence_blocks(self):
        r=assess(self.backtest,self.top25)
        self.assertEqual(r["status"],"blocked_for_publication")
        self.assertFalse(r["live_predictions_enabled"])
        self.assertEqual(len(r["missing_verification"]),len(REQUIRED_EVIDENCE))

    def test_untrusted_claims_do_not_unlock(self):
        claims={k:{"verified":True,"source":"self-declared"} for k in REQUIRED_EVIDENCE}
        r=assess(self.backtest,self.top25,claims)
        self.assertEqual(r["status"],"blocked_for_publication")
        self.assertEqual(len(r["untrusted_evidence_claims"]),len(REQUIRED_EVIDENCE))

    def test_invalid_counts_rejected(self):
        self.top25["hits"]=21
        with self.assertRaises(ValueError):
            assess(self.backtest,self.top25)

if __name__=="__main__":
    unittest.main()
