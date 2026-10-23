import unittest
from tools.analyze_horizontal_v1_4 import analyze,lag_summary
class V14Tests(unittest.TestCase):
 def test_sync_and_lag(self):
  self.assertEqual(lag_summary([10,20],[10,21]),(1,0.5))
 def test_complete_interval(self):
  sid="s";markers=[dict(session=sid,label="BEGIN_BASELINE",frame="3"),dict(session=sid,label="END_BASELINE",frame="5")]
  timeline=[dict(session=sid,offset_hex=offset,frame=str(f),raw_hex=raw)
   for offset in ("0x0D3995","0x0D3D3D") for f,raw in ((3,"00000000"),(4,"00000000"),(5,"00000000"))]
  rows=analyze(markers,timeline,sid)
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]["changes"],0)
 def test_gap_fails(self):
  sid="s";markers=[dict(session=sid,label="BEGIN_BASELINE",frame="3"),dict(session=sid,label="END_BASELINE",frame="5")]
  timeline=[dict(session=sid,offset_hex=offset,frame=str(f),raw_hex="00000000")
   for offset in ("0x0D3995","0x0D3D3D") for f in (3,5)]
  with self.assertRaises(ValueError):analyze(markers,timeline,sid)
