import unittest
from tools.analyze_horizontal_v1_2 import analyze,f32
class TemporalV12Tests(unittest.TestCase):
 def test_float_decoding(self):
  self.assertEqual(f32("000000C3"),-128.0)
  self.assertEqual(f32("00000000"),0.0)
 def test_bracketed_windows(self):
  sid="test"
  markers=[dict(session=sid,frame=str(n),label=label) for n,label in [(10,"BEGIN_AUTOAIM_OFF"),(12,"END_AUTOAIM_OFF"),(14,"STOP")]]
  timeline=[dict(session=sid,frame=str(frame),offset_hex=offset,raw_hex=raw)
   for frame,raw in [(10,"000000C3"),(11,"00000000"),(12,"00000000")]
   for offset in ("0x0D3995","0x0D3D3D")]
  results=analyze(markers,timeline,sid)
  self.assertEqual(len(results),2)
  self.assertEqual(results[0]["changes"],1)
  self.assertEqual(results[0]["samples"],3)
 def test_missing_end_rejected(self):
  with self.assertRaises(ValueError):
   analyze([dict(session="x",frame="1",label="BEGIN_TARGET_LEFT")],[],"x")
