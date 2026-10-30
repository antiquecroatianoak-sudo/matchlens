import unittest
from analytics.prior_xg import prior_xg_features
from analytics.factor_intake import validate_factor


def prior(match_id, xg, day):
    return {
        "match_id": match_id, "team_id": "club-a", "xg": xg, "source": "licensed-example",
        "match_end_at": f"2026-10-{day}T17:00:00Z",
        "published_at": f"2026-10-{day}T18:00:00Z",
    }


class PriorXgTests(unittest.TestCase):
    def test_only_prior_published_games(self):
        history = [prior("old1", 1, "10"), prior("old2", 2, "11"), prior("future", 99, "20")]
        fixture = [{"match_id": "target", "team_id": "club-a", "prediction_at": "2026-10-12T12:00:00Z"}]
        result = prior_xg_features(history, fixture, min_history=2)
        self.assertEqual(len(result["factors"]), 1)
        self.assertEqual(result["factors"][0]["value"], 1.5)
        self.assertEqual(validate_factor(result["factors"][0]), [])

    def test_no_same_match_leakage(self):
        history = [prior("target", 4, "10"), prior("old", 2, "09")]
        fixture = [{"match_id": "target", "team_id": "club-a", "prediction_at": "2026-10-12T12:00:00Z"}]
        result = prior_xg_features(history, fixture, min_history=1)
        self.assertEqual(result["factors"][0]["value"], 2)

    def test_missing_history_stays_missing(self):
        result = prior_xg_features([prior("old", 1, "10")], [{"match_id": "target", "team_id": "club-a", "prediction_at": "2026-10-12T12:00:00Z"}], min_history=2)
        self.assertEqual(len(result["factors"]), 0)
        self.assertEqual(len(result["missing"]), 1)

    def test_nonfinite_xg_rejected(self):
        result = prior_xg_features([prior("bad", float("nan"), "10"), prior("inf", float("inf"), "11")], [], min_history=1)
        self.assertEqual(len(result["rejected_history"]), 2)

    def test_duplicate_team_match_rejected(self):
        result = prior_xg_features([prior("old", 1, "10"), prior("old", 5, "10")], [], min_history=1)
        self.assertEqual(len(result["rejected_history"]), 1)

    def test_invalid_postmatch_publication_rejected(self):
        row = dict(prior("old", 1, "10"), published_at="2026-10-10T16:00:00Z")
        result = prior_xg_features([row], [], min_history=1)
        self.assertEqual(len(result["rejected_history"]), 1)

    def test_numeric_and_string_ids_reconcile(self):
        rows = [dict(prior(101, 1.5, "10"), team_id=7)]
        fixture = [{"match_id": 102, "team_id": "7", "prediction_at": "2026-10-12T12:00:00Z"}]
        result = prior_xg_features(rows, fixture, min_history=1)
        self.assertEqual(len(result["factors"]), 1)
        self.assertEqual(result["factors"][0]["value"], 1.5)

    def test_latest_match_end_not_latest_publication(self):
        rows = [prior("older", 1, "10"), prior("newer", 3, "11")]
        rows[0]["published_at"] = "2026-10-14T18:00:00Z"
        rows[1]["published_at"] = "2026-10-12T18:00:00Z"
        fixture = [{"match_id": "target", "team_id": "club-a", "prediction_at": "2026-10-15T12:00:00Z"}]
        result = prior_xg_features(rows, fixture, min_history=1, max_history=1)
        self.assertEqual(result["factors"][0]["value"], 3)


if __name__ == "__main__":
    unittest.main()
