import unittest
from tools.analyze_horizontal_v1 import analyze,LABELS
class HorizontalTests(unittest.TestCase):
 def test_replay_and_off_controls(self):
  data={key:bytes([10,40]) for key in LABELS}
  data.update(ON_LEFT=bytes([1,40]),ON_CENTER=bytes([2,40]),ON_RIGHT=bytes([3,40]),
              ON_LEFT_REPEAT=bytes([1,40]),OFF_LEFT=bytes([0,40]),OFF_CENTER=bytes([0,40]),OFF_RIGHT=bytes([0,40]))
  # Small synthetic data cannot pass production-size guard.
  with self.assertRaises(ValueError):analyze(data)
