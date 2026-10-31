import unittest
from scripts.settle_prospective_predictions import settle

class SettlementTests(unittest.TestCase):
    def test_finished_home_win(self):
        r={"id":"openligadb:123","predicted_outcome":"home"}
        m={"matchIsFinished":True,"matchResults":[{"resultTypeID":2,"pointsTeam1":2,"pointsTeam2":1}]}
        self.assertEqual(settle(r,m)["correct"],True)
    def test_pending_not_marked_wrong(self):
        self.assertEqual(settle({"id":"openligadb:123","predicted_outcome":"away"},None)["status"],"pending")
    def test_ambiguous_final_not_scored(self):
        m={"matchIsFinished":True,"matchResults":[]}
        self.assertEqual(settle({"id":"openligadb:123","predicted_outcome":"away"},m)["status"],"missing_unambiguous_final_score")
if __name__=="__main__":unittest.main()
