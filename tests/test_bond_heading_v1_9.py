import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_heading_v1_9 import analyze
class HeadingTests(unittest.TestCase):
 def test_rotation_specific(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s="demo";stem=root/"bond_heading_v1_9_demo"
   phases=["BASELINE_STILL","TURN_LEFT","STILL_LEFT","TURN_RIGHT","STILL_RETURN","MOVE_FORWARD","MOVE_BACK"]
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as h:
    w=csv.writer(h);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(40*len(phases)):
     p=n//40;t=n%40
     rot=float(t if p==1 else 40-t if p==3 else 0)
     pos=float(t if p==5 else 40-t if p==6 else 0)
     for off,v in [(0x0D3998,rot),(0x0D33EC,pos)]:
      w.writerow([s,n,phases[p],f"0x{off:06X}",struct.pack(">f",v).hex().upper(),0])
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,280,stop\n")
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
   r=analyze(s,root)
   self.assertTrue(r["complete"])
   item={x["offset"]:x for x in r["candidates"]}
   self.assertGreater(item["0X0D3998"]["rotation_specificity_score"],item["0X0D33EC"]["rotation_specificity_score"])
   self.assertFalse(r["heading_validated"])
 def test_invalid_sid(self):
  with self.assertRaises(ValueError):analyze("../x")
if __name__=="__main__":unittest.main()
