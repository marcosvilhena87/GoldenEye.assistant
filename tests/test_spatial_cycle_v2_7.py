import unittest
from tools.analyze_spatial_cycle_v2_7 import audit,aligned,compare,circular_null
from tools.analyze_spatial_position_v2_4 import START,END
class CycleTests(unittest.TestCase):
 def test_lag_direction(self):
  self.assertEqual(aligned([1,0,1,0],[0,1,0,1],1),([1,0,1],[1,0,1]))
 def test_phi_and_null(self):
  self.assertEqual(compare([1,0,1,0],[1,0,1,0])['phi'],1.0)
  self.assertTrue(len(circular_null([1,0]*20,[1,0]*20,0,9))>0)
 def test_all_phase_outputs(self):
  boundaries=[100+i*30 for i in range(10)]
  frames={}
  for f in range(boundaries[0],boundaries[-1]):
   row={o:0 for o in range(START,END+1)}
   for base in (0x3B30D0,0x3B30E0,0x3B30EC):row[base]=f%2
   frames[f]=row
  lead,cycle,group=audit('test',frames,boundaries,5)
  self.assertEqual(len(cycle),9*12*3)
  self.assertEqual(len(group),9*66)
  self.assertEqual(len(lead),9*(66+12*6))
  self.assertTrue(any(row['lag']==1 for row in lead))
 def test_short_phase_rejected(self):
  with self.assertRaises(ValueError):audit('t',{},[i*2 for i in range(10)],5)
if __name__=='__main__':unittest.main()
