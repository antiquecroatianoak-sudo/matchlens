import unittest
from analytics.active_strategy import load_active,replacement_decision


class ActiveStrategyTests(unittest.TestCase):
    def setUp(self):
        self.active=load_active()
        rows=[dict(id=str(i),hit=i%2==0) for i in range(200)]
        self.evidence=dict(kind='unused_chronological_validation',used_for_tuning=False,season='new-unseen',
                           coverage_policy=self.active['coverage_policy'],champion=rows,
                           challenger=[dict(id=str(i),hit=True) for i in range(200)])

    def test_registry_uses_archived_champion(self):
        self.assertEqual(self.active['id'],'market-specialists-v1')
        self.assertEqual(self.active['reference']['hits'],3455)
        self.assertFalse(self.active['live_recommendations_enabled'])

    def test_only_higher_comparable_accuracy_replaces(self):
        self.assertTrue(replacement_decision(self.active,{'id':'new'},self.evidence)['replace'])
        self.evidence['challenger']=self.evidence['champion']
        self.assertFalse(replacement_decision(self.active,{'id':'new'},self.evidence)['replace'])

    def test_easier_or_smaller_subset_cannot_replace(self):
        self.evidence['challenger']=self.evidence['challenger'][:10]
        self.assertFalse(replacement_decision(self.active,{'id':'new'},self.evidence)['replace'])
        self.evidence['champion']=self.evidence['champion'][:10]
        self.assertEqual(replacement_decision(self.active,{'id':'new'},self.evidence)['reason'],'insufficient_sample')

    def test_viewed_audit_cannot_activate_new_strategy(self):
        self.evidence['season']='2024-25'
        self.assertEqual(replacement_decision(self.active,{'id':'new'},self.evidence)['reason'],'previously_viewed_audit')
        self.evidence['season']='new-unseen';self.evidence['used_for_tuning']=True
        self.assertFalse(replacement_decision(self.active,{'id':'new'},self.evidence)['replace'])


if __name__=='__main__':unittest.main()
