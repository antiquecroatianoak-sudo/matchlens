import unittest
from datetime import date,timedelta
import numpy as np
from analytics.expanded_search import features,probability_array,fit,intensities,BASE,records_before,metrics


def sample_rows():
    rows=[]
    for i in range(220):
        day=(date(2020,1,1)+timedelta(days=i*3)).isoformat()
        rows.append(dict(id=str(i),date=day,season='2019-20' if i<120 else '2020-21',league='en.1',home='A' if i%2 else 'B',away='B' if i%2 else 'A',hg=i%4,ag=i%3,round=str(i)))
    return rows

class ExpandedSearchTests(unittest.TestCase):
    def test_features_ignore_target_and_future_results(self):
        rows=sample_rows();cutoff=rows[180]['date'];before=features(rows,20,15)
        after=features([{**r,'hg':9,'ag':8} if r['date']>=cutoff else r for r in rows],20,15)
        lookup={r['match']['id']:r for r in after}
        for r in before:
            if r['match']['date']<=cutoff:
                other=lookup[r['match']['id']]
                self.assertEqual(r['x'],other['x']);self.assertEqual(r['offset'],other['offset'])
                self.assertGreater((date.fromisoformat(r['match']['date'])-date.fromisoformat(r['history_end'])).days,2)

    def test_development_does_not_depend_on_audit_outcomes(self):
        from analytics.backtest import load_matches
        from analytics.expanded_search import evaluate_dev
        rows,_=load_matches('data/openfootball')
        rows=[r for r in rows if r['league']=='en.1']
        original=features(rows,50,15)
        mutated=features([{**r,'hg':8,'ag':7} if r['season']>='2024-25' else r for r in rows],50,15)
        lam,y,folds=evaluate_dev(original,BASE)
        other,other_y,other_folds=evaluate_dev(mutated,BASE)
        np.testing.assert_array_equal(lam,other)
        np.testing.assert_array_equal(y,other_y)
        self.assertEqual(folds,other_folds)

    def test_coherent_market_probabilities(self):
        for rho in (-.1,0,.1):
            for temp in (.85,1,1.15):
                p=probability_array(np.array([[.15,.15],[1.5,1.1],[6.,6.]]),rho,temp)
                self.assertTrue(np.all((p>0)&(p<1)))
                np.testing.assert_allclose(p[:,:3].sum(axis=1),1.)
                np.testing.assert_allclose(p[:,3:].sum(axis=1),1.)

    def test_season_training_boundary(self):
        rec=features(sample_rows(),20,15);train=records_before(rec,'2020-21')
        start=min(r['match']['date'] for r in rec if r['match']['season']=='2020-21')
        self.assertTrue(train)
        for r in train:
            self.assertLess(r['match']['season'],'2020-21')
            self.assertGreater((date.fromisoformat(start)-date.fromisoformat(r['match']['date'])).days,2)

    def test_training_and_metrics_use_separate_targets(self):
        rec=features(sample_rows(),20,15);train=rec[:50];val=rec[50:]
        model=fit(train,BASE);p=probability_array(intensities(val,model))
        changed=[{**r,'match':{**r['match'],'hg':10,'ag':10}} for r in val]
        np.testing.assert_array_equal(p,probability_array(intensities(changed,model)))
        from analytics.expanded_search import actual_array
        m=metrics(p,actual_array(val));self.assertEqual(m['matches'],len(val))
        self.assertTrue(0<=m['top_pick_hit_rate']<=1)

if __name__=='__main__':unittest.main()
