import unittest
from analytics.double_chance import probabilities,offers,settle,MARKET


class DoubleChanceTests(unittest.TestCase):
    generated='2026-10-29T12:00:00Z'
    kickoff='2026-10-30T12:00:00Z'
    def quote(self,**extra):
        return dict(dict(match_id='m',market=MARKET,selection='1X',odds=2.,source='synthetic-test',timestamp='2026-10-29T11:00:00Z'),**extra)
    def build(self,quotes):return offers('m',[.2,.3,.5],quotes,self.generated,self.kickoff)

    def test_probability_union_and_regular_time_settlement(self):
        self.assertEqual(probabilities([.2,.3,.5]),{'1X':.5,'X2':.8})
        for selection in ('1X','X2'):self.assertEqual(settle(selection,1,1),1)
        self.assertEqual(settle('1X',0,1),0)
        self.assertEqual(settle('X2',0,1),1)
        self.assertIsNone(settle('1X',None,None))

    def test_no_odds_no_offer_and_boundary_two(self):
        self.assertEqual(self.build([]),[])
        self.assertEqual(self.build([self.quote(odds=1.99)]),[])
        out=self.build([self.quote()]);self.assertEqual(len(out),1)
        self.assertEqual(out[0]['prob'],50.)
        self.assertNotIn('status',out[0])

    def test_exact_quote_identity_and_availability(self):
        for change in (dict(match_id='other'),dict(market='1X2'),dict(selection='2'),dict(source=''),dict(timestamp='2026-10-29T13:00:00Z'),dict(timestamp='2026-10-29T11:00:00')):
            self.assertEqual(self.build([self.quote(**change)]),[])

    def test_newer_sub_two_quote_retires_older_qualifying_quote(self):
        old=self.quote();new=self.quote(odds=1.9,timestamp='2026-10-29T11:30:00Z')
        self.assertEqual(self.build([old,new]),[])
        self.assertEqual(len(self.build([old,new,self.quote(source='other-source',odds=2.1)])),1)

    def test_invalid_probabilities_rejected(self):
        for p in ([.2,.2,.2],[.5,.5],[-.1,.6,.5],[float('nan'),.5,.5]):
            with self.assertRaises(ValueError):probabilities(p)


if __name__=='__main__':unittest.main()
