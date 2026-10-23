import unittest
from tools.analyze_horizontal_v1_3 import analyze
class CameraAimSeparationTests(unittest.TestCase):
 def test_fixed_and_moving_have_separate_classes(self):
  sid="test"
  markers=[{"session":sid,"label":label,"frame":str(frame)} for frame,label in
           [(10,"BEGIN_FIXED_CAMERA_ON_TARGET"),(12,"END_FIXED_CAMERA_ON_TARGET"),
            (13,"BEGIN_TURN_CAMERA_NO_TARGET"),(15,"END_TURN_CAMERA_NO_TARGET")]]
  timeline=[{"session":sid,"frame":str(frame),"offset_hex":off,"raw_hex":raw}
            for off in ("0x0D3995","0x0D3D3D")
            for frame,raw in [(10,"000000C3"),(11,"000000C2"),(12,"000000C2"),
                              (13,"000000C2"),(14,"000000C1"),(15,"000000C1")]]
  result=analyze(markers,timeline,sid)
  self.assertEqual(len(result),4)
  self.assertEqual(result[0]["camera_state"],"operator_declared_fixed")
  self.assertEqual(result[2]["camera_state"],"operator_declared_moving")
 def test_missing_frame_rejected(self):
  markers=[{"session":"s","label":"BEGIN_FIXED_CAMERA_CONTROL","frame":"1"},
           {"session":"s","label":"END_FIXED_CAMERA_CONTROL","frame":"3"}]
  rows=[{"session":"s","frame":str(i),"offset_hex":off,"raw_hex":"00000000"}
        for off in ("0x0D3995","0x0D3D3D") for i in (1,3)]
  with self.assertRaises(ValueError):analyze(markers,rows,"s")
