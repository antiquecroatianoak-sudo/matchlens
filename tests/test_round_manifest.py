import unittest
from scripts.validate_round_manifest import validate

class RoundManifestTests(unittest.TestCase):
    def test_matching_ids_do_not_self_certify(self):
        m={"rounds":[{"league":"en.1","season":"2024-25","round":"1",
            "scheduled_fixture_ids":["a","b"],"schedule_source":"independent fixture archive",
            "schedule_archived_at":"2024-08-01T00:00:00Z"}]}
        result=validate(m,{("en.1","2024-25","1"):["a","b"]})
        self.assertTrue(result["rounds"][0]["matches_manifest"])
        self.assertFalse(result["certified_complete_rounds"])
    def test_missing_fixture_fails(self):
        m={"rounds":[{"league":"en.1","season":"2024-25","round":"1",
            "scheduled_fixture_ids":["a","b"],"schedule_source":"archive",
            "schedule_archived_at":"2024-08-01T00:00:00Z"}]}
        result=validate(m,{("en.1","2024-25","1"):["a"]})
        self.assertEqual(result["rounds"][0]["missing_ids"],["b"])
        self.assertFalse(result["rounds"][0]["matches_manifest"])
    def test_no_provenance_rejected(self):
        m={"rounds":[{"league":"en.1","season":"2024-25","round":"1",
            "scheduled_fixture_ids":["a"]}]}
        with self.assertRaises(ValueError):
            validate(m,{})
if __name__=="__main__":unittest.main()
