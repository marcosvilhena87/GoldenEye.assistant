import unittest,struct
from pathlib import Path
from tempfile import TemporaryDirectory
from tools.analyze_spatial_position_v1_8 import classify,LABELS
from tools.send_spatial_v1_8 import send

def values():
 return (0,-2,-4,-4, -2,0,0, 5,10,10, 5,0,0, 0)

class PositionDiscoveryTests(unittest.TestCase):
 def test_two_axes(self):
  r=classify(values())
  self.assertEqual(r["classification"],"two_axes_unverified")
  self.assertTrue(r["lateral_opposite"])
  self.assertTrue(r["longitudinal_opposite"])
 def test_rotation_sensitive_rejected(self):
  vals=list(values());vals[-1]=9
  self.assertIsNone(classify(vals))
 def test_no_progress_rejected(self):
  vals=list(values());vals[1]=vals[2]
  result=classify(vals)
  self.assertTrue(result is None or result["classification"]=="forward_axis_unverified")
 def test_unstable_hold_rejected(self):
  vals=list(values());vals[3]=999
  self.assertIsNone(classify(vals))
 def test_sender_enforces_order(self):
  with TemporaryDirectory() as folder:
   root=Path(folder)
   for name in ("output/commands","output/sessions","output/csv"):
    (root/name).mkdir(parents=True,exist_ok=True)
   (root/"output/sessions/spatial_v1_8_session.txt").write_text("test\n")
   with self.assertRaises(ValueError):send("LEFT_MID",root)
   send("BASELINE_STILL",root)
   with self.assertRaises(ValueError):send("STOP",root)
   send("LEFT_MID",root)
if __name__=="__main__":unittest.main()
