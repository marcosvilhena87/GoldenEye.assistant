import unittest
from tools.analyze_spatial_shared_source_v2_8 import audit, determinism, compare_flags, null_control
from tools.analyze_spatial_position_v2_4 import START, END

class SharedSourceV28Tests(unittest.TestCase):
 def test_dependency(self):
  self.assertEqual(determinism([0,0,1,1],[2,2,3,3]),1)
  self.assertEqual(determinism([0,0],[2,3]),0.5)
 def test_cochange(self):
  c=compare_flags([1,0,1,0],[1,0,1,0])
  self.assertEqual(c[4],1)
  self.assertEqual(c[5],1)
 def test_phase_outputs_and_null(self):
  bounds=[100+i*32 for i in range(10)]
  frames={}
  for f in range(bounds[0],bounds[-1]):
   row={o:0 for o in range(START,END+1)}
   row[0x3B30D0]=f%2
   row[0x3B30E0]=f%2
   row[0x3B30EC]=(f//3)%2
   frames[f]=row
  blocks,values,events=audit('test',frames,bounds,7)
  self.assertEqual((len(blocks),len(values),len(events)),(27,27,27))
  item=next(x for x in blocks if x['phase']=='P0_HOLD' and x['left']=='0x3B30D0' and x['right']=='0x3B30E0')
  self.assertEqual(item['phi'],1)
  self.assertEqual(item['byte_mask_equal_fraction'],1)
  self.assertEqual(item['shared_changed_byte_fraction'],1)
  dep=next(x for x in values if x['phase']=='P0_HOLD' and x['left']=='0x3B30D0' and x['right']=='0x3B30E0')
  self.assertEqual(dep['forward_determinism'],1)
  self.assertEqual(dep['reverse_determinism'],1)
 def test_invalid_trial_count(self):
  with self.assertRaises(ValueError):audit('test',{},[],2)
if __name__=='__main__':unittest.main()
