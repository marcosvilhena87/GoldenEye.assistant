import csv,struct,tempfile,unittest
from pathlib import Path
from tools.audit_bond_alias_v1_8_15 import audit
class AliasOrderingTests(unittest.TestCase):
 def test_a_leads_b_single_frame(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);path=root/"bond_position_v1_8_13_demo_timeline.csv"
   with path.open("w",newline="") as h:
    w=csv.writer(h);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(8):
     a=0.0 if n<3 else 10.0
     b=0.0 if n<4 else 10.0
     for off,v in {0x06D248:a,0x06D250:a+20,0x0D33EC:b,0x0D33F4:b+20}.items():
      w.writerow(["demo",n,"MOVE_FORWARD",f"0x{off:06X}",struct.pack(">f",v).hex().upper(),0])
   r=audit("demo",root)
   self.assertEqual(r["divergence_count"],1)
   self.assertEqual(r["change_events"],2)
   self.assertEqual(r["divergence_frames"][0]["one_frame_ordering"],"A_first")
   self.assertFalse(r["ordering_validated"])
 def test_unsafe_sid(self):
  with self.assertRaises(ValueError):audit("../bad")
if __name__=="__main__":unittest.main()
