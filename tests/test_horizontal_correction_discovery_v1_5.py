import unittest
from tools.analyze_horizontal_v1_5 import analyze, lag_summary, OFFSETS

class CameraAimV15Tests(unittest.TestCase):
 def test_same_frame_and_lag(self):
  self.assertEqual(lag_summary([4,10],[4,12]),(1,1.0))
 def test_complete_fixed_window(self):
  sid="test";markers=[{"session":sid,"label":"BEGIN_FIXED_NO_TARGET","frame":"10"},{"session":sid,"label":"END_FIXED_NO_TARGET","frame":"12"}]
  timeline=[{"session":sid,"frame":str(f),"offset_hex":offset,"raw_hex":"00000000"} for offset in OFFSETS for f in range(10,13)]
  rows=analyze(markers,timeline,sid)
  self.assertEqual(len(rows),len(OFFSETS))
  self.assertTrue(all(r["changes"]==0 for r in rows))
  self.assertEqual(rows[0]["operator_camera_condition"],"declared_fixed")
 def test_gap_rejected(self):
  sid="test";markers=[{"session":sid,"label":"BEGIN_TURN_LEFT_NO_TARGET","frame":"10"},{"session":sid,"label":"END_TURN_LEFT_NO_TARGET","frame":"12"}]
  timeline=[{"session":sid,"frame":str(f),"offset_hex":offset,"raw_hex":"00000000"} for offset in OFFSETS for f in (10,12)]
  with self.assertRaises(ValueError):analyze(markers,timeline,sid)
 def test_incomplete_marker_rejected(self):
  with self.assertRaises(ValueError):analyze([{"session":"x","label":"BEGIN_FIXED_NO_TARGET","frame":"1"}],[],"x")
if __name__=="__main__":unittest.main()
