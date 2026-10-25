import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_heading_v1_9_1 import audit
class HeadingVectorTests(unittest.TestCase):
 def test_retro_and_pair(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);sid="demo";prefix=root/"bond_heading_v1_9_demo"
   phases=["BASELINE_STILL"]*40+["TURN_LEFT"]*40+["STILL_LEFT"]*40
   with Path(str(prefix)+"_timeline.csv").open("w",newline="") as h:
    w=csv.writer(h);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for i,p in enumerate(phases):
     ang=min(max(i-40,0),39)/39*1.5
     for addr,val in ((0x0D33F8,math_cos(ang)),(0x0D33FC,math_sin(ang)),
                      (0x0D3998,float(i%4)),(0x0D3D40,float(i%4)-2)):
      w.writerow([sid,i,p,f"0x{addr:06X}",struct.pack(">f",val).hex().upper(),0])
   Path(str(prefix)+"_termination.csv").write_text("session,frame,reason\ndemo,120,stop\n")
   r=audit(sid,root)
   self.assertTrue(r["complete"])
   self.assertAlmostEqual(r["fields"]["0x0D33F8"]["TURN_LEFT"]["last_float"],math_cos(1.5),places=5)
   pair=next(p for p in r["vector_pair_hypotheses"] if p["a"]=="0x0D33F8" and p["b"]=="0x0D33FC")
   self.assertLess(pair["r2_spread"],0.00001)
   self.assertFalse(r["heading_validated"])
 def test_sid_traversal(self):
  with self.assertRaises(ValueError):audit("../demo")
def math_sin(x):
 import math
 return math.sin(x)
def math_cos(x):
 import math
 return math.cos(x)
if __name__=="__main__":unittest.main()
