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

    def test_odd_sized_certified_round_selects_ceil_quarter(self):
        rows=self.rows[:5]
        result=select(rows,self.now,lambda *args:{r["id"] for r in rows})
        self.assertEqual(sum(r["top25"] for r in result),2)

    def test_duplicate_fixture_blocks_certification(self):
        result=select(self.rows+[self.rows[0]],self.now,lambda *args:{r["id"] for r in self.rows})
        self.assertEqual(sum(r["top25"] for r in result),0)

    def test_partial_round_never_marks_top25(self):
        rows=self.rows[:5]
        expected={r['id'] for r in self.rows}
        result=select(rows,self.now,lambda *args:expected)
        self.assertEqual(len(result),5)
        self.assertTrue(all(not r['top25'] for r in result))
        self.assertTrue(all(not r['round_certified'] for r in result))

    def test_unavailable_provider_blocks_selection(self):
        result=select(self.rows,self.now,lambda *args:None)
        self.assertEqual(sum(r["top25"] for r in result),0)

    def test_less_than_one_hour_before_kickoff_is_excluded(self):
        rows=[{**self.rows[0],"kickoff_utc":(self.now+timedelta(minutes=59)).isoformat()}]
        self.assertEqual(select(rows,self.now,lambda *args:{"openligadb:0"}),[])

    def test_exactly_one_hour_before_kickoff_is_allowed(self):
        rows=[{**self.rows[0],"kickoff_utc":(self.now+timedelta(hours=1)).isoformat()}]
        result=select(rows,self.now,lambda *args:{"openligadb:0"})
        self.assertEqual(len(result),1)
        self.assertTrue(result[0]["top25"])

    def test_no_after_kickoff(self):
        rows=[{**self.rows[0],"kickoff_utc":self.now.isoformat()}]
        self.assertEqual(select(rows,self.now,lambda *args:{"openligadb:0"}),[])

if __name__=="__main__":
    unittest.main()
