import csv,tempfile,unittest
from pathlib import Path
from tools.analyze_spatial_position_v1_9 import evaluate,run,PHASES,ADDRS
class SpatialV19Tests(unittest.TestCase):
 def records(self,rotation=0):
  samples=[]
  defs={"BASELINE_HOLD":[100]*5,"FORWARD":[100,102,104,106,108],
        "FORWARD_HOLD":[108]*5,"BACK":[108,106,104,102,100],
        "BACK_HOLD":[100]*5,"ROTATE":[100,100+rotation/4,100+rotation/2,100+3*rotation/4,100+rotation],
        "ROTATE_HOLD":[100+rotation]*5,"STRAFE":[100+rotation]*5,"STRAFE_HOLD":[100+rotation]*5}
  for phase,values in defs.items():
   for address in ADDRS:
    for val in values:samples.append({"address":address,"phase":phase,"be_float32":str(val)})
  return samples
 def test_reproduced_is_still_unverified(self):
  rows=evaluate(self.records())
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]["classification"],"candidate_reproduced_unverified")
 def test_rotation_detected(self):
  self.assertEqual(evaluate(self.records(3))[0]["classification"],"rotation_sensitive_unverified")
 def test_missing_phase_fails(self):
  with self.assertRaises(ValueError):evaluate([r for r in self.records() if r["phase"]!="BACK_HOLD"])
 def test_incomplete_session_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/"output/csv";folder.mkdir(parents=True)
   with (folder/"spatial_v1_9_test_termination.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["reason"]);w.writeheader();w.writerow({"reason":"frame_limit"})
   with self.assertRaises(ValueError):run("test",Path(tmp))
if __name__=="__main__":unittest.main()
