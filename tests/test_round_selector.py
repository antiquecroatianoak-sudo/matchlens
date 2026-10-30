import unittest
from analytics.round_selector import choose_round, backtest
def match(i,p1=.6,px=.2,p2=.2,po=.5):
    return {"match_id":str(i),"prediction_at":"2025-01-01T10:00:00Z",
      "probabilities":{"1":p1,"X":px,"2":p2,"over_2_5":po},
      "odds":{m:{"price":1.5,"available_at":"2025-01-01T09:00:00Z"} for m in ("1","X","2","over_2_5","under_2_5")},
      "home_goals":2,"away_goals":0}
class RoundSelectorTests(unittest.TestCase):
    def test_25_percent_and_one_tip(self):
        picks=choose_round([match(i) for i in range(8)])
        self.assertEqual(len(picks),2)
        self.assertEqual(len({p["match_id"] for p in picks}),2)
    def test_regular_price_strict(self):
        m=match(1);m["odds"]={k:{"price":1.30,"available_at":"2025-01-01T09:00:00Z"} for k in m["odds"]}
        self.assertEqual(choose_round([m]),[])
    def test_synthetic_threshold(self):
        m=match(1,.15,.20,.65,.5);m["odds"]={}
        self.assertEqual(choose_round([m])[0]["market"],"1X")
    def test_late_quotes(self):
        m=match(1);m["odds"]={k:{"price":2.0,"available_at":"2025-01-01T11:00:00Z"} for k in m["odds"]}
        self.assertEqual(choose_round([m]),[])
    def test_joint_accuracy(self):
        r=backtest([{"round_id":"r1","matches":[match(i) for i in range(4)]}])
        self.assertEqual(r["selected"],1)
        self.assertEqual(r["accuracy"],1)
if __name__=="__main__":unittest.main()
