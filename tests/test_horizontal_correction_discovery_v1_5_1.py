import unittest
from tools.analyze_horizontal_v1_5_1 import analyze, OFFSETS

class TimelineIntegrityTests(unittest.TestCase):
 def data(self,frames=(10,11,12)):
  sid="test"
  m=[dict(session=sid,label="BEGIN_FIXED_NO_TARGET",sample_index="1",frame=str(frames[0])),dict(session=sid,label="END_FIXED_NO_TARGET",sample_index="3",frame=str(frames[-1]))]
  t=[dict(session=sid,sample_index=str(i+1),frame=str(f),offset_hex=o,raw_hex="00000000") for i,f in enumerate(frames) for o in OFFSETS]
  return m,t,sid
 def test_contiguous(self):
  m,t,s=self.data();r=analyze(m,t,s)
  self.assertEqual(len(r),len(OFFSETS))
  self.assertEqual(r[0]["begin_sample_index"],1)
 def test_frame_rollback_rejected(self):
  m,t,s=self.data((10,11,4))
  with self.assertRaisesRegex(ValueError,"frame gap/reset"):analyze(m,t,s)
 def test_frame_jump_rejected(self):
  m,t,s=self.data((10,11,14))
  with self.assertRaisesRegex(ValueError,"frame gap/reset"):analyze(m,t,s)
 def test_sample_gap_rejected(self):
  m,t,s=self.data()
  t=[r for r in t if not (r["sample_index"]=="2" and r["offset_hex"]==OFFSETS[0])]
  with self.assertRaisesRegex(ValueError,"frame gap/reset"):analyze(m,t,s)
 def test_unclosed_action_rejected(self):
  m,t,s=self.data()
  with self.assertRaisesRegex(ValueError,"incomplete action"):analyze(m[:1],t,s)
if __name__=="__main__":unittest.main()
