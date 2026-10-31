import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_prematch_evidence import audit

class PrematchEvidenceAuditTests(unittest.TestCase):
    def test_claims_never_become_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"2024-25.en.1.json").write_text(json.dumps({"matches":[
                {"date":"2025-01-01","round":"1","score":{"ft":[1,0]}},
                {"date":"2025-01-02","round":"1","prediction_created_at":"2025-01-01T12:00:00Z",
                 "bookmaker_odds":{"home":1.8},"prematch_factors":{str(i):i for i in range(11)}}
            ]}))
            result=audit(folder)
            c=result["counts"]
            self.assertEqual(c["fixtures"],2)
            self.assertEqual(c["round_labels"],2)
            self.assertEqual(c["prediction_timestamp_claims"],1)
            self.assertEqual(c["odds_claims"],1)
            self.assertEqual(c["factor_claims_11_plus"],1)
            self.assertFalse(result["timestamped_prematch_predictions_verified"])
            self.assertFalse(result["historical_executable_odds_verified"])

if __name__=="__main__":
    unittest.main()
