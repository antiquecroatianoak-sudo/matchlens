import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from analytics.league_factor_search import NEW_GROUPS,NEW_CANDIDATES,load_offers,run
from analytics.backtest import MARKETS

class LeagueFactorSearchTests(unittest.TestCase):
    def test_new_groups_add_context_and_remove_current_elo(self):
        self.assertEqual(NEW_GROUPS['full_context'],list(range(9)))
        self.assertNotIn(7,NEW_GROUPS['without_current_elo'])
        self.assertEqual(NEW_GROUPS['attack_defence_only'],[0,1])

    def test_old_trials_not_counted_as_new(self):
        self.assertEqual(len(NEW_CANDIDATES),36)
        self.assertEqual({r['id'] for r in NEW_CANDIDATES},set(range(13,49)))
        self.assertTrue(all(0<r['alpha']<=1 for r in NEW_CANDIDATES))

    def test_predictions_join_by_identity_not_row_order(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'p.jsonl';rows=[]
            for name,value in [('b',.2),('a',.8)]:
                rows.extend(dict(match_id=name,market=k,prob=value) for k in MARKETS)
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            actual=load_offers(p,[dict(match=dict(id='a')),dict(match=dict(id='b'))])
            np.testing.assert_array_equal(actual,np.array([[.8]*5,[.2]*5]))
            with self.assertRaises(KeyError):load_offers(p,[dict(match=dict(id='missing'))])

    def test_changed_source_cannot_reuse_old_development_trials(self):
        with tempfile.TemporaryDirectory() as d:
            previous=Path(d)/'prior';previous.mkdir();(previous/'league-report.json').write_text(json.dumps(dict(protocol=dict(source_sha256='different'))))
            with patch('analytics.league_factor_search.all_fixtures',return_value=([],{})):
                with self.assertRaisesRegex(ValueError,'Source changed'):
                    run('unused','unused',previous,Path(d)/'out',Path(d)/'ui.json')

if __name__=='__main__':unittest.main()
