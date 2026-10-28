import unittest
from analytics.backtest import load_matches,walk,predict,probabilities,CONFIGS,apply_calibration,fit_calibration
class BacktestTests(unittest.TestCase):
 def test_probability_consistency(self):
  for lh,la in ((.15,.15),(1.5,1.1),(6,6)):
   p=probabilities(lh,la);self.assertAlmostEqual(sum(p[k] for k in ('home','draw','away')),1);self.assertAlmostEqual(p['over2.5']+p['under2.5'],1)
 def test_future_and_same_day_results_do_not_change_prediction(self):
  rows,_=load_matches('data/openfootball');rows=[r for r in rows if r['league']=='en.1'][:180];before=walk(rows,CONFIGS[0]);cutoff=before[-20]['date'];changed=[{**r,'hg':15,'ag':12} if r['date']>=cutoff else r.copy() for r in rows];after=walk(changed,CONFIGS[0]);a={r['id']:r for r in after}
  for r in before:
   if r['date']<=cutoff:self.assertEqual(r['prob'],a[r['id']]['prob'])
 def test_embargo(self):
  from datetime import date
  rows,_=load_matches('data/openfootball')
  for r in walk([r for r in rows if r['league']=='en.1'][:180],CONFIGS[0]):self.assertGreater((date.fromisoformat(r['date'])-date.fromisoformat(r['history_end'])).days,2)
 def test_calibration_uses_only_supplied_training_rows(self):
  rows,_=load_matches('data/openfootball');pred=walk([r for r in rows if r['league']=='en.1'][:180],CONFIGS[0]);table=fit_calibration(pred[:20]);a=apply_calibration(pred[20:21],table);changed=[{**r,'actual':{k:1-v for k,v in r['actual'].items()}} for r in pred[20:21]];b=apply_calibration(changed,table);self.assertEqual(a[0]['prob'],b[0]['prob'])
if __name__=='__main__':unittest.main()

class ImportTests(unittest.TestCase):
 def test_upstream_zero_draw_and_postponed(self):
  from analytics.import_upstream import parse
  rows=parse('▪ Matchday 1\n Sat Aug 16 2025\n 12:30 A FC v B FC 0-0\n 15:00 C FC v D FC [postponed]\n', '2025-26')
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['score']['ft'],[0,0]);self.assertEqual(rows[0]['date'],'2025-08-16')
 def test_upstream_rejects_conflicting_duplicate(self):
  from analytics.import_upstream import parse
  with self.assertRaises(ValueError):parse(' Sat Aug 16 2025\n A v B 1-0\n A v B 2-0\n','2025-26')
