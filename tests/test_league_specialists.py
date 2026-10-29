import unittest
from datetime import date
from unittest.mock import patch
import numpy as np
from analytics.league_specialists import choose,local_predictions,cluster_interval
from analytics.expanded_search import features
from tests.test_expanded_search import sample_rows

class LeagueSpecialistTests(unittest.TestCase):
    def test_weak_league_uses_pooled_even_if_local_development_score_is_better(self):
        trials=[dict(config=dict(id=0,alpha=0),score=.8),dict(config=dict(id=1,alpha=1),score=.1)]
        selected,reason=choose(trials,199)
        self.assertEqual(selected['config']['id'],0)
        self.assertEqual(reason,'insufficient_development_matches')
        self.assertEqual(choose(trials,200)[0]['config']['id'],1)

    def test_selection_uses_only_development_not_audit(self):
        trials=[dict(config=dict(id=0,alpha=0),score=.8,audit=0),dict(config=dict(id=1,alpha=1),score=.7,audit=1)]
        self.assertEqual(choose(trials,300)[0]['config']['id'],1)
        trials[0]['audit']=1;trials[1]['audit']=0
        self.assertEqual(choose(trials,300)[0]['config']['id'],1)

    def test_local_history_embargo_and_target_outcome_isolation(self):
        records=features(sample_rows(),20,15);targets=[r for r in records if r['match']['season']=='2020-21']
        pooled=np.tile([.4,.3,.3,.5,.5],(len(targets),1))
        config=dict(window=20,half_life=15,ridge=.01,group='snaga',rho=0,temperature=1)
        policy=dict(refit='season',half_life_days=None)
        with patch('analytics.league_specialists.MIN_TRAIN',10):
            p,_,trace=local_predictions(records,'2020-21',config,policy,.01,pooled)
            changed=[{**r,'match':{**r['match'],'hg':9,'ag':8}} if r['match']['season']=='2020-21' else r for r in records]
            q,_,_=local_predictions(changed,'2020-21',config,policy,.01,pooled)
        np.testing.assert_array_equal(p,q)
        np.testing.assert_allclose(p[:,:3].sum(axis=1),1.)
        for t in trace:
            self.assertGreater((date.fromisoformat(t['cutoff'])-date.fromisoformat(t['training_last_date'])).days,2)

    def test_insufficient_local_training_preserves_pooled_probabilities(self):
        records=features(sample_rows(),20,15);targets=[r for r in records if r['match']['season']=='2020-21']
        pooled=np.tile([.4,.3,.3,.5,.5],(len(targets),1))
        p,_,trace=local_predictions(records,'2020-21',dict(group='snaga'),dict(refit='season'),.01,pooled)
        np.testing.assert_array_equal(p,pooled)
        self.assertTrue(all(t['fallback_to_pooled'] for t in trace))

    def test_match_cluster_interval_retains_shared_fixture_groups(self):
        rows=[dict(match_id='a',actual=1),dict(match_id='a',actual=0),dict(match_id='b',actual=1)]
        interval=cluster_interval(rows)
        self.assertEqual(len(interval),2);self.assertGreaterEqual(interval[0],.5);self.assertLessEqual(interval[1],1)

if __name__=='__main__':unittest.main()
