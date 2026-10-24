import unittest
from tools.analyze_spatial_position_v2_2 import examine
from tools.analyze_spatial_position_v2_0 import ADDRS,PHASES

class SpatialV22Tests(unittest.TestCase):
 def data(self,periodic):
  marks=list(range(10,110,10))
  by_frame={}
  for f in range(10,100):
   k=(f-10)%10
   v=("00000001" if k%2 else "00000000") if periodic else "00000000"
   by_frame[f]={a:v for a in ADDRS}
  return by_frame,marks
 def test_recurrence(self):
  d,m=self.data(True)
  rows=examine("test",d,m,max_lag=3,permutations=20,seed=4)
  r=next(x for x in rows if x["lag"]==2)
  self.assertEqual(r["raw_match_rate"],1)
  self.assertGreater(r["excess_match"],0)
 def test_constant_not_falsely_periodic(self):
  d,m=self.data(False)
  rows=examine("test",d,m,max_lag=2,permutations=20)
  self.assertEqual(rows[0]["excess_match"],0)
 def test_reject_bad_parameters(self):
  d,m=self.data(True)
  with self.assertRaises(ValueError):examine("test",d,m,max_lag=0)
if __name__=="__main__":unittest.main()
