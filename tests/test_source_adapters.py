import unittest
from analytics.source_adapters import lineup_features, prematch_context

CUTOFF = "2025-10-01T16:00:00Z"
KICKOFF = "2025-10-01T18:00:00Z"

def lineup(available="2025-10-01T15:00:00Z"):
    return dict(kind="confirmed_lineup", source_id="club-official", match_id="m1", team_id="t1",
                published_at=available, available_at=available,
                starting_player_ids=["p"+str(i) for i in range(11)])

class SourceAdapterTests(unittest.TestCase):
    def test_eligible_lineup(self):
        self.assertEqual(len(lineup_features(lineup(), CUTOFF, KICKOFF)["starting_player_ids"]), 11)

    def test_late_lineup_is_unavailable(self):
        self.assertIsNone(lineup_features(lineup("2025-10-01T17:00:00Z"), CUTOFF, KICKOFF))

    def test_duplicate_players_rejected(self):
        row = lineup()
        row["starting_player_ids"][10] = "p0"
        with self.assertRaises(ValueError):
            lineup_features(row, CUTOFF, KICKOFF)

    def test_missing_sources_remain_missing(self):
        self.assertEqual(prematch_context(None, None, None, CUTOFF, KICKOFF),
                         {"weather": None, "pitch": None, "lineup": None})

if __name__ == "__main__":
    unittest.main()
