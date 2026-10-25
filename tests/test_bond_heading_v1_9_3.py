import csv,math,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_heading_v1_9_3 import reconstruct,principal
class AngularReconstructionTests(unittest.TestCase):
 def test_wrap_and_turn(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sid="demo";stem=root/"bond_heading_v1_9_2_demo"
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for i in range(101):
     phase="BASELINE_STILL" if i<10 else "TURN_LEFT_90" if i<90 else "HOLD_90"
     ang=math.radians(170+max(0,i-10)*0.5)
     for o,v in ((0x0D33F8,math.cos(ang)),(0x0D3400,math.sin(ang))):
      w.writerow([sid,i,phase,f"0x{o:06X}",struct.pack(">f",v).hex().upper(),0])
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,101,stop\n")
   report,rows=reconstruct(sid,root)
   self.assertTrue(report["complete"])
   steps=[r["step_deg"] for r in rows if r["step_deg"] is not None and r["phase"]=="TURN_LEFT_90"]
   self.assertTrue(all(s>=-0.001 for s in steps))
   self.assertGreater(sum(steps),38)
   self.assertTrue(any(r["angle_deg"]<0 for r in rows))
   self.assertFalse(report["heading_physically_calibrated"])
 def test_principal(self):
  self.assertAlmostEqual(principal(-358),2)
  self.assertAlmostEqual(principal(358),-2)
 def test_sid(self):
  with self.assertRaises(ValueError):reconstruct("../bad")
if __name__=="__main__":unittest.main()
