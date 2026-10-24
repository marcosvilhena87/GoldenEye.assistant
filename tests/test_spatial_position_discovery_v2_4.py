import unittest
from tools.analyze_spatial_position_v2_4 import audit,decode,START,END
class ControlledMovementTests(unittest.TestCase):
 def test_decode(self):
  self.assertEqual(decode(bytes.fromhex("3F800000"),"be_f32"),1.)
  self.assertEqual(decode(bytes.fromhex("0001"),"be_u16"),1)
 def test_controlled_sequence(self):
  bounds=list(range(0,1800,180))
  data={}
  # Nine phases, static positions P0=0 P1=12 RETURN=0 ROTATED=0 P2=12.
  phase_pos={0:0,1:6,2:12,3:6,4:0,5:0,6:0,7:6,8:12}
  for frame in range(1620):
   phase=frame//180;v=phase_pos[phase]
   bytes4=int(v).to_bytes(4,"big")
   data[frame]={o:0 for o in range(START,END+1)}
   for i,b in enumerate(bytes4):data[frame][START+i]=b
  result=audit("test",data,bounds,tail=120)
  r=next(x for x in result if x["offset"]==f"0x{START:06X}" and x["type"]=="be_i32")
  self.assertEqual(r["step1"],12)
  self.assertEqual(r["step_back"],-12)
  self.assertEqual(r["status"],"experimental_candidate")
 def test_short_hold_rejected(self):
  with self.assertRaises(ValueError):audit("test",{},list(range(10)),tail=5)
if __name__=="__main__":unittest.main()
