import csv,math,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_heading_v1_9_2 import analyze
class CycleTests(unittest.TestCase):
 def test_circle_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sid="demo";base=root/"bond_heading_v1_9_2_demo"
   with Path(str(base)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for i in range(240):
     phase="BASELINE_STILL" if i<40 else "TURN_LEFT_90" if i<140 else "TURN_LEFT_180"
     a=max(0,i-40)*2*math.pi/200
     for o,v in ((0x0D33F8,math.cos(a)),(0x0D33FC,math.sin(a)),(0x0D33EC,200.0)):
      w.writerow([sid,i,phase,f"0x{o:06X}",struct.pack(">f",v).hex().upper(),0])
   Path(str(base)+"_termination.csv").write_text("session,frame,reason\ndemo,240,stop\n")
   Path(str(base)+"_markers.csv").write_text("session,frame,label\n")
   r=analyze(sid,root)
   self.assertTrue(r["complete"])
   p=next(x for x in r["orthogonal_candidates"] if x["other"]=="0x0D33FC")
   self.assertTrue(p["candidate_unit_circle"])
   self.assertFalse(r["orthogonal_validated"])
 def test_path_traversal(self):
  with self.assertRaises(ValueError):analyze("../bad")
if __name__=="__main__":unittest.main()
