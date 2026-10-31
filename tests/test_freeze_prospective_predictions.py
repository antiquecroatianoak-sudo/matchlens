import unittest
from datetime import datetime, timezone, timedelta
from scripts.freeze_prospective_predictions import select

class ProspectiveSelectionTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,31,tzinfo=timezone.utc)
        self.rows=[{"id":f"openligadb:{i}","league":"bl1","season":"2026","round":"9",
            "kickoff_utc":(self.now+timedelta(days=1)).isoformat(),
            "prob":{"home":.1+i*.01,"draw":.2,"away":.7-i*.01},"model":"test"} for i in range(8)]

    def test_incomplete_round_never_publishes_top25(self):
        result=select(self.rows,self.now,lambda *args:{r["id"] for r in self.rows}|{"openligadb:99"})
        self.assertEqual(sum(r["top25"] for r in result),0)
        self.assertTrue(all(not r["round_certified"] for r in result))

    def test_complete_round_selects_two_of_eight(self):
        result=select(self.rows,self.now,lambda *args:{r["id"] for r in self.rows})
        self.assertEqual(sum(r["top25"] for r in result),2)
        self.assertTrue(all(r["round_certified"] for r in result))

    def test_duplicate_fixture_blocks_certification(self):
        result=select(self.rows+[self.rows[0]],self.now,lambda *args:{r["id"] for r in self.rows})
        self.assertEqual(sum(r["top25"] for r in result),0)

    def test_unavailable_provider_blocks_selection(self):
        result=select(self.rows,self.now,lambda *args:None)
        self.assertEqual(sum(r["top25"] for r in result),0)

    def test_no_after_kickoff(self):
        rows=[{**self.rows[0],"kickoff_utc":self.now.isoformat()}]
        self.assertEqual(select(rows,self.now,lambda *args:{"openligadb:0"}),[])

if __name__=="__main__":
    unittest.main()
