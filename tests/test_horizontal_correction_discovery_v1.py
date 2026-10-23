import unittest
from tools.analyze_horizontal_v1 import analyze,LABELS
class HorizontalTests(unittest.TestCase):
 def test_replay_and_off_controls(self):
  size=8388608
  inputs={key:bytearray(size) for key in LABELS}
  inputs["ON_LEFT"][3]=1
  inputs["ON_CENTER"][3]=2
  inputs["ON_RIGHT"][3]=3
  inputs["ON_LEFT_REPEAT"][3]=1
  result=analyze(inputs)
  self.assertEqual(len(result),1)
  self.assertEqual(result[0]["offset_hex"],"0x000003")
 def test_inconsistent_replay_rejected(self):
  size=8388608
  inputs={key:bytearray(size) for key in LABELS}
  inputs["ON_LEFT"][3]=1
  inputs["ON_CENTER"][3]=2
  inputs["ON_RIGHT"][3]=3
  inputs["ON_LEFT_REPEAT"][3]=7
  self.assertEqual(analyze(inputs),[])
