import json,tempfile,unittest
from pathlib import Path
from tools.verify_autoaim_consolidation_v1_6 import verify
class ConsolidationTests(unittest.TestCase):
 def test_safe_reference(self):
  source={"status":"experimentally_reproduced","operational_permission":"none","rom_identity_verified":False,
          "candidate_offsets":[{"offset_hex":o,"status":("experimentally_reproduced" if i<3 else "needs_validation")} for i,o in enumerate(("0x040A93","0x0D308B","0x0D309B","0x067D37","0x069AAD"))],
          "evidence_sessions":[{"session":"20261023T213220Z_234487","frames":[{}]*6},{"session":"20261023T215226Z_301601"}],
          "summary":{"principal_offset_transitions_in_controls":0}}
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/"record.json";path.write_text(json.dumps(source))
   self.assertEqual(verify(path)["candidate_count"],5)
   source["operational_permission"]="write"
   path.write_text(json.dumps(source))
   with self.assertRaises(ValueError):verify(path)
