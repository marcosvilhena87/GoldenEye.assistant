import unittest
from tools.analyze_spatial_replication_v3_0 import audit,PAIRS
from tools.analyze_spatial_position_v2_4 import START,END

class ReplicationV30Tests(unittest.TestCase):
 def make(self,offset):
  markers=[100+i*36 for i in range(10)]
  frames={}
  for f in range(markers[0],markers[-1]):
   row={a:0 for a in range(START,END+1)}
   row[0x3B30D0]=((f//3)+offset)%2
   row[0x3B30E0]=((f//3)+offset)%2
   for left,right in PAIRS[1:]:
    row[left]=(f+offset)%7
    row[right]=((f//5)+offset)%11
   frames[f]=row
  return frames,markers
 def test_no_self_replication(self):
  a,ma=self.make(0)
  with self.assertRaises(ValueError):audit('A','A',a,ma,a,ma)
 def test_independent_session_outputs(self):
  a,ma=self.make(0)
  b,mb=self.make(1)
  rows,summary=audit('A','B',a,ma,b,mb)
  self.assertEqual(len(rows),9*len(PAIRS)*2)
  self.assertEqual(len(summary),len(PAIRS))
  self.assertEqual(sum(r['pair_type']=='candidate' for r in summary),1)
  self.assertTrue(all(r['test_frames']>0 for r in rows))
 def test_metrics_not_automatically_validated(self):
  a,ma=self.make(0)
  b,mb=self.make(0)
  rows,_=audit('A','B',a,ma,b,mb)
  self.assertTrue(any(r['feature']=='change_mask' and r['accuracy_gain']>=0 for r in rows))
if __name__=='__main__':unittest.main()
