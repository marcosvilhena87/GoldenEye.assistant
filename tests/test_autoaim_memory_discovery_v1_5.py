import unittest
from tools.analyze_autoaim_mem_v1_5 import analyze,OFFSETS
class V15Tests(unittest.TestCase):
 def test_bracketed_readings(self):
  samples=[{"frame":str(frame),"offset_hex":off,"byte":str((0 if frame==2 else 1))} for frame in range(5) for off in OFFSETS]
  markers=[dict(frame="1",phase="BEGIN",action="AUTOAIM_OFF"),dict(frame="3",phase="END",action="AUTOAIM_OFF")]
  result=analyze(samples,markers)
  self.assertEqual(len(result),5)
  self.assertEqual(result[0]["inside_changes"],1)
  self.assertEqual(result[0]["before_byte"],1)
 def test_unclosed_window(self):
  with self.assertRaises(ValueError):
   analyze([{"frame":"1","offset_hex":o,"byte":"1"} for o in OFFSETS],
     [dict(frame="1",phase="BEGIN",action="AUTOAIM_ON")])
