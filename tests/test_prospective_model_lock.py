import json
import tempfile
import unittest
from pathlib import Path
from analytics.prospective_model_lock import read_factor_lock, ModelLockError


class ProspectiveModelLockTests(unittest.TestCase):
    def check(self, payload):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lock.json'
            path.write_text(json.dumps(payload))
            return read_factor_lock(path)

    def test_valid_selection(self):
        p={'protocol':'factor-search-v1','features':84,
           'chosen':{f:{'config':{'group':'all','leaves':7,'l2':10.}} for f in ('outcome','goals')},
           'temperatures':{'outcome':1.,'goals':.85}}
        self.assertEqual(len(self.check(p)['outcome']['columns']),84)

    def test_missing_selection_rejected(self):
        with self.assertRaises(ModelLockError):
            self.check({'protocol':'factor-search-v1','features':84})

    def test_wrong_feature_count_rejected(self):
        with self.assertRaises(ModelLockError):
            self.check({'protocol':'factor-search-v1','features':38})


if __name__=='__main__':
    unittest.main()
