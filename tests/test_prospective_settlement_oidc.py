import io
import json
import unittest
from unittest.mock import patch
from scripts import sync_prospective_settlement_oidc as mod

class SettlementSyncTests(unittest.TestCase):
    @patch.object(mod, "identity", return_value="test-token")
    @patch.object(mod, "urlopen")
    def test_settlement_endpoint_response(self, opener, _identity):
        opener.return_value.__enter__.return_value = io.BytesIO(
            json.dumps({"checked":2,"settled":2,"pending_final":0}).encode())
        mod.main()
        req=opener.call_args.args[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(json.loads(req.data),{"action":"settle"})
        self.assertEqual(req.get_header("Authorization"),"Bearer test-token")

    @patch.object(mod, "identity", return_value="test-token")
    @patch.object(mod, "urlopen")
    def test_invalid_settlement_response_fails(self, opener, _identity):
        opener.return_value.__enter__.return_value = io.BytesIO(b'{"error":"not processed"}')
        with self.assertRaises(RuntimeError):
            mod.main()

if __name__=="__main__":
    unittest.main()
