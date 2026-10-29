import unittest
from analytics.person_matchups import PersonHistory,validate

def coach(i=1,team='old',points=0,available='2020-02-02T00:00:00Z'):
    return dict(record_id=str(i),source_id='test-only',match_id='m'+str(i),occurred_at='2020-02-01T20:00:00Z',available_at=available,team_id=team,opponent_id='opponent',coach_id='coach',points=points,expected_points=2,baseline_generated_at='2020-02-01T19:00:00Z',baseline_version='frozen-test')
def duel(i=1,attacker='a',defender='d',success=0,team='old'):
    return dict(record_id=str(i),source_id='test-only',match_id='m'+str(i),occurred_at='2020-02-01T20:00:00Z',available_at='2020-02-02T00:00:00Z',team_id=team,opponent_id='opponent',attacker_id=attacker,defender_id=defender,event_type='dribble',attacker_role='wing',defender_role='fullback',pair_evidence='explicit_link',success=success)

class PersonMatchupTests(unittest.TestCase):
    def test_coach_transfers_keep_identity_not_club(self):
        h=PersonHistory([coach(i) for i in range(6)])
        a=h.coach('coach','new','opponent','2021-01-01T00:00:00Z','target')
        self.assertEqual(a['cross_club_matches'],6);self.assertTrue(a['supported']);self.assertLess(a['value'],0)
        self.assertIsNone(h.coach('different','new','opponent','2021-01-01T00:00:00Z','target')['value'])

    def test_future_availability_and_target_outcome_excluded(self):
        r=coach(2,available='2022-01-01T00:00:00Z');target=coach(3);target['match_id']='target'
        h=PersonHistory([coach(),r,target]);a=h.coach('coach','new','opponent','2021-01-01T00:00:00Z','target')
        self.assertEqual(a['matches'],1)

    def test_pair_history_across_clubs_and_comparison_baselines(self):
        pairs=[duel(i) for i in range(6)]+[duel(20+i,defender='other'+str(i),success=1) for i in range(10)]+[duel(40+i,attacker='other'+str(i),success=1) for i in range(10)]
        h=PersonHistory(duels=pairs);a=h.pair('a','d','new','2021-01-01T00:00:00Z','target','dribble','wing','fullback')
        self.assertEqual(a['cross_club_matches'],6);self.assertTrue(a['supported']);self.assertLess(a['value'],0)
        self.assertIsNone(h.pair('a','d','new','2021-01-01T00:00:00Z','target','aerial','wing','fullback')['value'])

    def test_many_events_one_match_are_not_many_games(self):
        records=[duel(i) for i in range(100)]
        for r in records:r['match_id']='same'
        a=PersonHistory(duels=records).pair('a','d','new','2021-01-01T00:00:00Z','target','dribble','wing','fullback')
        self.assertEqual(a['matches'],1);self.assertFalse(a['supported']);self.assertLess(a['effective_weight'],1)

    def test_duplicate_or_inferred_duels_rejected(self):
        with self.assertRaises(ValueError):PersonHistory(duels=[duel(),duel()])
        r=duel();r['pair_evidence']='same_lineup'
        with self.assertRaises(ValueError):validate(r,'duel')

    def test_coach_baseline_must_be_pre_match(self):
        r=coach();r['baseline_generated_at']=r['occurred_at']
        with self.assertRaises(ValueError):validate(r,'coach')

    def test_missing_data_remains_missing(self):
        h=PersonHistory();self.assertIsNone(h.coach('c','t','o','2021-01-01T00:00:00Z','x')['value'])

    def test_future_lineup_is_rejected(self):
        t=dict(match_id='x',team_id='new',opponent_id='opponent',coach_id='coach',as_of='2021-01-01T00:00:00Z',coach_known_at='2020-12-01T00:00:00Z',expected_pairs=[{}],lineup_known_at='2021-01-01T01:00:00Z')
        with self.assertRaises(ValueError):PersonHistory().target(t)

if __name__=='__main__':unittest.main()

class PersonTargetTests(unittest.TestCase):
    def test_small_samples_not_exposed_as_ready_model_effects(self):
        t=dict(match_id='target',team_id='new',opponent_id='opponent',coach_id='coach',as_of='2021-01-01T00:00:00Z',coach_known_at='2020-12-01T00:00:00Z')
        r=PersonHistory([coach()]).target(t)
        self.assertFalse(r['model_ready']);self.assertIsNone(r['model_columns']['coach_opponent_residual'])
        self.assertIsNone(r['model_columns']['player_pair_residual'])

    def test_same_coach_match_from_multiple_sources_not_counted_twice(self):
        a=coach();b=coach();b['source_id']='second';b['record_id']='other-record'
        with self.assertRaises(ValueError):PersonHistory([a,b])
