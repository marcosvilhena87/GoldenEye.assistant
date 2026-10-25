import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_ai_causality_v1_8_16 import analyze
class CausalityTests(unittest.TestCase):
 def test_decoupling_and_release(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"bond_ai_causality_v1_8_16_demo"
   labels=["AI_FREEZE_CONFIRMED","DECOUPLE_MOVE","DECOUPLE_BOND_STILL",
           "SOLDIER_OLD_TARGET","AI_RELEASE_REQUEST","AI_RELEASE_CONFIRMED",
           "BOND_STILL_POST_RELEASE","SOLDIER_RETARGET_OBSERVED"]
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as h:
    w=csv.writer(h);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(len(labels)*40):
     p=n//40;value=0.0 if p==0 else (n%40)*2.0 if p==1 else 78.0
     a=0.0 if p<=3 else value
     for o,v in {0x06D248:a,0x06D250:a,0x0D33EC:value,0x0D33F4:value}.items():
      w.writerow(["demo",n,labels[p],f"0x{o:06X}",struct.pack(">f",v).hex().upper(),0])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,320,stop\n")
   r=analyze("demo",root)
   self.assertTrue(r["complete"])
   self.assertTrue(r["freeze_phase_A_constant"])
   self.assertTrue(r["bond_still_after_release_B_constant"])
   self.assertFalse(r["causality_validated"])
 def test_bad_sid(self):
  with self.assertRaises(ValueError):analyze("../demo")
if __name__=="__main__":unittest.main()
