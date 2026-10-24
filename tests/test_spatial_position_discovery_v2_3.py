import tempfile,unittest
from pathlib import Path
from tools.analyze_spatial_position_v2_3 import audit,decode,load,run,START,END

class SpatialV23Tests(unittest.TestCase):
 def test_decode_endianness(self):
  self.assertEqual(decode(bytes.fromhex("3F800000"),"f32",">"),1.0)
  self.assertEqual(decode(bytes.fromhex("0001"),"u16",">"),1)
  self.assertEqual(decode(bytes.fromhex("0001"),"u16","<"),256)
 def test_cross_phase_reconstruction(self):
  markers=[10,20,30,40,50,60]
  frames={}
  for f in range(10,60):
   b={address:0 for address in range(START,END+1)}
   v=(f-20)*2 if 20<=f<30 else 0
   b[START:START] if False else None
   b[START]=v & 255
   b[START+1]=0
   frames[f]=b
  summary,bound=audit("test",frames,markers)
  self.assertEqual(len(summary), (80//2)*2*2+(80//4)*2*3)
  self.assertEqual(len(bound),len(summary)*4)
  cand=next(x for x in summary if x["offset"]==f"0x{START:06X}" and x["interpretation"]=="be_u16")
  self.assertGreater(cand["move_change_rate"],cand["still_change_rate"])
  self.assertEqual(cand["status"],"experimental_unverified")
 def test_missing_session(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(FileNotFoundError):load("missing",Path(t))
if __name__=="__main__":unittest.main()
