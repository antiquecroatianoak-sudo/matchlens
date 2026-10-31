import unittest
from unittest.mock import patch
import numpy as np
from analytics.prospective_factors import prepare_future_design


class ProspectiveFactorsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {'id': 'future-1', 'date': '2026-10-31', 'league': 'de.1',
                        'home': 'Bayern', 'away': 'Dortmund'}
        self.history = [
            {'id': 'old', 'date': '2024-09-01', 'season': '2024-25',
             'league': 'de.1', 'home': 'Bayern', 'away': 'Dortmund', 'hg': 1, 'ag': 0},
            {'id': 'too-old', 'date': '2023-09-01', 'season': '2023-24',
             'league': 'de.1', 'home': 'Bayern', 'away': 'Dortmund', 'hg': 2, 'ag': 1},
            {'id': 'future', 'date': '2026-11-01', 'season': '2026-27',
             'league': 'de.1', 'home': 'Bayern', 'away': 'Dortmund', 'hg': 2, 'ag': 2},
        ]

    def test_two_seasons_and_future_results_excluded(self):
        def fake_features(rows, window, half_life):
            self.assertEqual([r['id'] for r in rows if not r.get('pending')], ['old'])
            self.assertTrue(rows[-1]['pending'])
            return [{'match': rows[-1]}]
        with patch('analytics.prospective_factors.features', side_effect=fake_features), \
             patch('analytics.prospective_factors.build_design', return_value=np.ones((1,84))):
            accepted, skipped = prepare_future_design(self.history, [self.fixture])
        self.assertEqual(skipped, [])
        self.assertEqual(len(accepted[0]['features']), 84)
        self.assertEqual(accepted[0]['history_seasons'], ['2024-25', '2025-26'])

    def test_unknown_team_skips(self):
        fixture = {**self.fixture, 'away': 'Unknown'}
        accepted, skipped = prepare_future_design(self.history, [fixture])
        self.assertFalse(accepted)
        self.assertEqual(len(skipped), 1)


if __name__ == '__main__':
    unittest.main()
