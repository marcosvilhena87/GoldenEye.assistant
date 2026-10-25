import csv,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_spatial_v1_8_6 import analyze
class TestSpatial(unittest.TestCase):
 def test_identical_series_detected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"soldier_spatial_v1_8_6_synthetic"
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as out:
    w=csv.writer(out);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(6):
     for o in ("0x001000","0x001020"):
      w.writerow(["synthetic",n,"SOLDIER_MOVE",o,"41200000" if n<2 else "41400000",int(n==2)])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\nsynthetic,0,SOLDIER_MOVE\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\nsynthetic,6,stop\n")
   result=analyze("synthetic",root)
   self.assertTrue(result["capture_complete"])
   self.assertEqual(result["top_pairs"][0]["same_raw_fraction"],1.0)
   self.assertFalse(result["xyz_validated"])
if __name__=="__main__":unittest.main()
