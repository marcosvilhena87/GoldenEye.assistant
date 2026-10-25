import csv,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_identity_v1_8_7 import analyze
class TestIdentityFreeze(unittest.TestCase):
 def test_freeze_quiet_and_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"soldier_identity_v1_8_7_demo"
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(10):
     for o in ("0x06A120","0x20F578","0x20F594","0x20F5AC","0x20F580","0x06A128"):
      w.writerow(["demo",n,"FREEZE_REQUEST_ON",o,"3F800000" if n<3 else "40000000",int(n==3)])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\ndemo,2,FREEZE_REQUEST_ON\ndemo,9,STOP\n")
   Path(str(stem)+"_termination.csv").write_text("session,9,stop\n")
   result=analyze("demo",root,quiet_frames=3)
   self.assertTrue(result["capture_complete"])
   self.assertTrue(result["freeze_episodes"][0]["fields"]["0x20F594"]["quiet_window_observed"])
   self.assertEqual(result["duplicate_pairs"][0]["equal_fraction"],1.0)
if __name__=="__main__":unittest.main()
