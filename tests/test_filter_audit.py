import unittest
from analytics.filter_audit import select,summary

def item(id,p,actual=1,day='2025-01-01'):
    return dict(id=id,match_id=id.split('|')[0],date=day,season='2024-25',league='en.1',market='home',prob=p,actual=actual)

class FilterAuditTests(unittest.TestCase):
    def test_selection_is_daily_and_allows_same_fixture(self):
        rows=[item('A|home',.9),item('A|under',.85),item('B|home',.8),item('C|home',.95,day='2025-01-02')]
        chosen=select(rows,dict(top=2,threshold=0))
        self.assertEqual([r['id'] for r in chosen],['A|home','A|under','C|home'])

    def test_unknown_outcomes_stay_in_ranking_pool(self):
        rows=[item('A|home',.95,None),item('B|home',.9,0),item('C|home',.8,1)]
        chosen=select(rows,dict(top=2,threshold=0));r=summary(chosen,rows)
        self.assertEqual((r['selected'],r['scored'],r['unscored'],r['hits'],r['misses']),(2,1,1,0,1))

    def test_outcomes_cannot_change_selection_and_ties_are_stable(self):
        rows=[item('B|home',.8,0),item('A|home',.8,1)]
        a=select(rows,dict(top=1,threshold=.8))
        b=select([{**r,'actual':None} for r in reversed(rows)],dict(top=1,threshold=.8))
        self.assertEqual(a[0]['id'],b[0]['id'])

    def test_empty_selection_has_no_invented_accuracy(self):
        r=summary([], [item('A|home',.6)])
        self.assertIsNone(r['hit_rate']);self.assertEqual(r['selected'],0)

if __name__=='__main__':unittest.main()
