import csv,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_chase_v1_8_8_1 import analyze
class ChaseTests(unittest.TestCase):
 def test_uncontrolled_chase_and_duplicates(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);stem=root/"soldier_chase_v1_8_8_1_demo"
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(8):
     for off in ("0x06A120","0x20F578","0x20F594"):
      w.writerow(["demo",n,"SOLDIER_CHASE" if n<4 else "FREEZE_REQUEST_ON",off,"3F800000" if n<3 else "40000000",int(n==3)])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\ndemo,4,FREEZE_REQUEST_ON\ndemo,8,STOP\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,8,stop\n")
   result=analyze("demo",root)
   self.assertTrue(result["capture_complete"])
   self.assertEqual(result["duplicate_pairs"][0]["equal_fraction"],1.0)
   self.assertFalse(result["axes_validated"])
if __name__=="__main__":unittest.main()
