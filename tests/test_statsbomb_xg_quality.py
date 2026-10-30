import unittest
from scripts.extract_statsbomb_features import extract


def shot(value):
    return {"team": {"id": 10, "name": "Example"}, "type": {"name": "Shot"}, "shot": {"statsbomb_xg": value}}


class XgExtractionQualityTests(unittest.TestCase):
    def test_valid_shot_xg_is_summed(self):
        result = extract(123, [shot(0.2), shot(0.4)])
        self.assertAlmostEqual(result[0]["xg_sum"], 0.6)
        self.assertEqual(result[0]["shots"], 2)

    def test_invalid_xg_fails_closed(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    extract(123, [shot(value)])


if __name__ == "__main__":
    unittest.main()
