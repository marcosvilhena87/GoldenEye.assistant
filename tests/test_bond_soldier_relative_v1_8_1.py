"""Minimal contract tests for soldier v1.8.1 using temporary v1.6 audit."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.analyze_bond_soldier_relative_v1_8_1 import analyze

SID = "test_001"
def sample():
    return {"protocol":"bond_soldier_relative_v1_8_1","runs":[{
        "bond_session":SID,"bond_target":"0x0D33EC",
        "freeze":{"on_verified_before":True,"on_verified_after":True,
                  "no_toggle_during_trial":True,"enemy_identity_stable":True},
        "soldier":{"id":"guard1","candidate":"manual-test",
                   "source":"independent_enemy_position_candidate",
                   "coordinate_candidate_independently_validated":True,
                   "before":{"u":10,"v":20},"after":{"u":10,"v":20}},
        "max_stationarity_drift":0.01,
        "bond_in_soldier_frame":{"independent_measurement":True,
                                "derived_from_ec_f4":False,"frame_matches_soldier":True,
                                "before":{"u":1,"v":2},"after":{"u":3,"v":2}}
    }]}

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        audit={"isolated_memory_effect":True,"target":"0x0D33EC",
               "candidate_changes":[{"float32_be_delta":128}]}
        (self.root/f"bond_position_v1_3_{SID}_coordinate_v1_6.json").write_text(json.dumps(audit))
    def tearDown(self):
        self.temp.cleanup()
    def test_controlled_stationary_soldier(self):
        r=analyze(sample(),self.root)
        self.assertEqual(r["eligible_runs"],1)
        self.assertEqual(r["runs"][0]["relative_vector"]["delta"],[-2.0,0.0])
        self.assertEqual(r["runs"][0]["relative_vector"]["inverse_agreement_error"],0)
        self.assertFalse(r["canonical_axis_validated"])
    def test_freeze_claim_alone_is_insufficient(self):
        data=sample()
        data["runs"][0]["soldier"]["coordinate_candidate_independently_validated"]=False
        self.assertEqual(analyze(data,self.root)["eligible_runs"],0)
    def test_soldier_drift_blocks_stationary_reference(self):
        data=sample()
        data["runs"][0]["soldier"]["after"]["u"]=12
        self.assertEqual(analyze(data,self.root)["eligible_runs"],0)
    def test_ec_f4_derived_bond_position_rejected(self):
        data=sample()
        data["runs"][0]["bond_in_soldier_frame"]["derived_from_ec_f4"]=True
        self.assertEqual(analyze(data,self.root)["eligible_runs"],0)

if __name__=="__main__":
    unittest.main()
