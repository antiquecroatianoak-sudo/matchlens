import unittest
from datetime import datetime, timezone, timedelta
from scripts.freeze_prospective_predictions import select

class ProspectiveSelectionTests(unittest.TestCase):
    def test_incomplete_round_never_publishes_top25(self):
        now = datetime(2026, 10, 31, tzinfo=timezone.utc)
        rows = [{"id":str(i),"league":"bl1","season":"2026","round":"9",
                 "kickoff_utc":(now+timedelta(days=1)).isoformat(),
                 "prob":[.1, .2, .7-i*.01], "model":"test"} for i in range(8)]
        result=select(rows,now)
        self.assertEqual(sum(r["top25"] for r in result),0)
        self.assertTrue(all(r["predicted_at_utc"]==now.isoformat() for r in result))
    def test_no_after_kickoff(self):
        now=datetime(2026,10,31,tzinfo=timezone.utc)
        self.assertEqual(select([{"id":"1","league":"bl1","season":"2026","round":"9",
          "kickoff_utc":now.isoformat(),"prob":[.2,.3,.5]}],now),[])

if __name__=="__main__":
    unittest.main()
