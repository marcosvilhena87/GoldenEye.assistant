import unittest
from tools.analyze_spatial_position_v1_7_4 import audit,OFFSETS
from tools.send_spatial_v1_7_4 import send,LABELS
from pathlib import Path
from tempfile import TemporaryDirectory

class SpatialPositionV174Tests(unittest.TestCase):
 def fixture(self):
  s="test"
  markers=[dict(session=s,sample_index=str(i),frame=str(100+i),label=lab,action="MOVE_LEFT",phase="BEGIN" if i==1 else "END")
    for i,lab in ((1,"BEGIN_MOVE_LEFT"),(4,"END_MOVE_LEFT"))]
  t=[]
  for index in range(1,6):
   for off in OFFSETS:
    value="3F800000" if index==2 and off==OFFSETS[0] else "00000000"
    t.append(dict(session=s,sample_index=str(index),frame=str(100+index),
                  action="MOVE_LEFT" if index<4 else "NONE",offset_hex=off,raw_hex=value))
  term=[dict(session=s,reason="stop",active_action="NONE")]
  return s,markers,t,term
 def test_temporal_phases(self):
  sid,m,t,term=self.fixture()
  rows=audit(m,t,term,[],sid)
  self.assertEqual(len(rows),8)
  self.assertEqual(rows[0]["samples"],3)
  self.assertEqual(rows[0]["end_sample"],3)
  self.assertEqual(rows[0]["raw_changes"],2)
 def test_reject_incomplete(self):
  sid,m,t,term=self.fixture()
  with self.assertRaises(ValueError):audit(m[:1],t,term,[],sid)
 def test_reject_discontinuity(self):
  sid,m,t,term=self.fixture()
  with self.assertRaises(ValueError):audit(m,t,term,[{"frame":"4"}],sid)
 def test_sender_enforces_brackets(self):
  with TemporaryDirectory() as d:
   root=Path(d)
   for folder in ("output/commands","output/sessions","output/csv"):
    (root/folder).mkdir(parents=True,exist_ok=True)
   (root/"output/sessions/spatial_v1_7_4_session.txt").write_text("test\n")
   self.assertIn("BEGIN_MOVE_LEFT",LABELS)
   send("BEGIN_MOVE_LEFT",root)
   with self.assertRaises(ValueError):send("BEGIN_MOVE_RIGHT",root)
   send("END_MOVE_LEFT",root)
   send("STOP",root)
if __name__=="__main__":unittest.main()
