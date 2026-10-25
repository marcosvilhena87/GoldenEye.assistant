import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_motion_v1_8_12 import analyze
class BondMotionTests(unittest.TestCase):
 def test_still_rotation_and_translation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"soldier_motion_v1_8_12_demo"
   phases=("STILL_BEFORE","ROTATE_LEFT","STILL_AFTER_LEFT","ROTATE_RIGHT",
           "STILL_AFTER_RIGHT","TRANSLATE_FORWARD","STILL_AFTER_FORWARD",
           "TRANSLATE_BACK","STILL_AFTER_BACK","ROTATE_REPEAT","STILL_FINAL")
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(len(phases)*40):
     stage=n//40;t=n%40;p=phases[stage]
     x=(t/10 if "ROTATE" in p else t*3 if p=="TRANSLATE_FORWARD"
        else 120-t*3 if p=="TRANSLATE_BACK" else 0.0)
     values={0x06D248:x,0x0D33EC:x,0x06D250:50.0,0x0D33F4:50.0,
             0x20F594:200.0,0x20F578:200.0,0x06A120:200.0,
             0x20F5AC:100.0,0x20F580:100.0,0x06A128:100.0}
     for off,value in values.items():
      w.writerow(["demo",n,p,f"0x{off:06X}",struct.pack(">f",value).hex().upper(),1])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,440,stop\n")
   report=analyze("demo",root)
   self.assertTrue(report["capture_complete"])
   self.assertTrue(report["candidate_pairs"]["historical"]["soldier_constant_across_phases"])
   self.assertTrue(report["candidate_pairs"]["historical"]["rotation_response_present"])
   self.assertTrue(report["candidate_pairs"]["historical"]["translation_response_present"])
   self.assertEqual(report["raw_alias_equalities"]["0x06D248__0x0D33EC"]["equal_fraction"],1)
   self.assertFalse(report["physical_coordinates_validated"])
 def test_reject_invalid_session(self):
  with self.assertRaises(ValueError):analyze("../unsafe")
if __name__=="__main__":unittest.main()
