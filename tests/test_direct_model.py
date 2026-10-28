import unittest
import numpy as np
from tests.test_expanded_search import sample_rows
from analytics.expanded_search import features,actual_array
from analytics.direct_model import history_extras,design,fit_direct,predict_direct

class DirectModelTests(unittest.TestCase):
    def test_extended_factors_exclude_target_and_future_results(self):
        rows=sample_rows();cut=rows[180]['date'];rec=features(rows,50,15)
        a=history_extras(rows,rec)
        changed=[{**r,'hg':9,'ag':8} if r['date']>=cut else r for r in rows]
        b=history_extras(changed,features(changed,50,15))
        for r in rec:
            if r['match']['date']<=cut:np.testing.assert_array_equal(a[r['match']['id']],b[r['match']['id']])

    def test_direct_probabilities_are_coherent_and_target_independent(self):
        rows=sample_rows();rec=features(rows,50,15);x=design(rec,history_extras(rows,rec));y=actual_array(rec)
        self.assertEqual(x.shape[1],38)
        m=fit_direct(x[:50],y[:50],list(range(38)),.1)
        for temp in (.75,1.,1.5):
            p=predict_direct(x[50:],m,temp)
            self.assertTrue(np.all((p>=0)&(p<=1)))
            np.testing.assert_allclose(p[:,:3].sum(axis=1),1)
            np.testing.assert_allclose(p[:,3:].sum(axis=1),1)

if __name__=='__main__':unittest.main()
