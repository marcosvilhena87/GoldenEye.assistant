import unittest
from tools.analyze_spatial_position_v2_5 import audit,summary
from tools.analyze_spatial_position_v2_4 import START,END

class ValidationTests(unittest.TestCase):
 def test_temporal_metrics(self):
  x=summary([1,1,2,2,3],"s",START,2,"be_i16","FORWARD")
  self.assertEqual(x["change_rate"],0.5)
  self.assertEqual(x["net_delta"],2)
 def test_second_forward_absent_is_not_validated(self):
  bounds=[i*130 for i in range(10)]
  # All nine phases: hold0=0, hold1=12, return=0, rotated=0, p2=0.
  poses=[0,6,12,6,0,0,0,0,0]
  frames={}
  for f in range(bounds[-1]):
   phase=f//130
   mem={o:0 for o in range(START,END+1)}
   for addr in (0x3B30D0,0x3B30E0):
    mem[addr]=poses[phase]
   frames[f]=mem
  _,checks=audit("test",frames,bounds)
  hit=next(r for r in checks if r["address"]=="0x3B30D0" and r["interpretation"]=="be_i16")
  self.assertEqual(hit["step2"],0)
  self.assertEqual(hit["second_shift"],False)
  self.assertEqual(hit["status"],"inconclusive_or_contradicted")
 def test_invalid_tail(self):
  with self.assertRaises(ValueError):audit("s",{},[],tail=5)
if __name__=="__main__":unittest.main()
