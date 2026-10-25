import csv,struct,tempfile,unittest
from pathlib import Path
from tools.audit_bond_position_v1_8_14 import analyze

class AliasAuditTests(unittest.TestCase):
 def test_alias_mismatch_and_opposing_vectors(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"bond_position_v1_8_13_demo"
   phases=["MOVE_FORWARD","MOVE_BACK"]
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as h:
    w=csv.writer(h);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(80):
     p=phases[n//40];t=n%40
     x=float(t if p=="MOVE_FORWARD" else 39-t)
     raw=lambda v:struct.pack(">f",v).hex().upper()
     values={0x06D248:x,0x0D33EC:x+(1 if n==12 else 0),0x06D250:2*x,0x0D33F4:2*x}
     for off,value in values.items():
      w.writerow(["demo",n,p,f"0x{off:06X}",raw(value),int(t>0)])
   report=analyze("demo",root)
   self.assertEqual(report["aliases"][0]["divergence_count"],1)
   self.assertEqual(report["divergence_frames"][0]["frame"],12)
   route=report["routes"]["primary"]["MOVE_FORWARD_vs_MOVE_BACK"]
   self.assertAlmostEqual(route["opposition_cosine"],-1)
   self.assertAlmostEqual(route["vector_closure_error"],0)
   self.assertFalse(report["physical_return_validated"])
 def test_unsafe_sid(self):
  with self.assertRaises(ValueError):analyze("../invalid")
if __name__=="__main__":unittest.main()
