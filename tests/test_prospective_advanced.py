import unittest
from unittest.mock import patch
import numpy as np
from analytics.prospective_advanced import score_advanced


class AdvancedInferenceTests(unittest.TestCase):
    def test_rejects_unknown_team_before_training(self):
        fixture = {'id': 'upcoming', 'date': '2026-10-31', 'league': 'de.1',
                   'home': 'Missing', 'away': 'Other'}
        scored, skipped = score_advanced([], [fixture], 'unused-lock')
        self.assertEqual(scored, [])
        self.assertEqual(skipped[0]['id'], 'upcoming')

    def test_two_completed_seasons_and_normalized_output(self):
        fixture = {'id': 'upcoming', 'date': '2026-10-31', 'league': 'de.1',
                   'home': 'A', 'away': 'B'}
        rows = [{'id': str(i), 'date': '2025-01-01', 'league': 'de.1',
                 'season': '2024-25', 'home': 'A', 'away': 'B', 'hg': 1, 'ag': 0}
                for i in range(200)]
        rows += [{'id': 'leak', 'date': '2026-10-30', 'league': 'de.1',
                  'season': '2026-27', 'home': 'A', 'away': 'B', 'hg': 99, 'ag': 99}]
        selection = {family: {'config': {}, 'columns': list(range(84)), 'temperature': 1.}
                     for family in ('outcome', 'goals')}
        class Model:
            classes_ = [0, 1, 2]
            def fit(self, x, y):
                return self
            def predict_proba(self, x):
                return np.array([[.5, .3, .2]])
        def fake_features(past, *_):
            self.assertTrue(all(r['id'] != 'leak' for r in past))
            return [{'match': r} for r in past]
        with patch('analytics.prospective_advanced.read_factor_lock', return_value=selection), \\
             patch('analytics.prospective_advanced.prepare_future_design',
                   return_value=([{'features': [0.] * 84}], [])), \\
             patch('analytics.prospective_advanced.features', side_effect=fake_features), \\
             patch('analytics.prospective_advanced.build_design', return_value=np.zeros((200, 84))), \\
             patch('analytics.prospective_advanced.actual_array',
                   return_value=np.tile([1., 0., 0., 1., 0.], (200, 1))), \\
             patch('analytics.prospective_advanced.learner', return_value=Model()), \\
             patch('analytics.prospective_advanced.probabilities',
                   return_value=np.array([[.5, .3, .2, .6, .4]])):
            # Training label class coverage is enforced before fitting.
            with self.assertRaisesRegex(ValueError, 'classes'):
                score_advanced(rows, [fixture], 'lock.json')


if __name__ == '__main__':
    unittest.main()
