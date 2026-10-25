import csv,tempfile,unittest,struct
from pathlib import Path
from tools.analyze_soldier_direction_v1_8_8 import analyze
class DirectionalTests(unittest.TestCase):
 def test_opposed_a_and_quiet(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"soldier_direction_v1_8_8_demo"
   labels=["AXIS_A_POS","AXIS_A_NEG","AXIS_B_POS","AXIS_B_NEG","STATIONARY"]
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(50):
     group=n//10;step=n%10
     v=100+step if group==0 else 110-step if group==1 else 100
     raw=struct.pack(">f",float(v)).hex().upper()
     w.writerow(["demo",n,labels[group],"0x20F594",raw,int(step>0 and group<2)])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,50,stop\n")
   r=analyze("demo",root,min_frames=5)
   self.assertTrue(r["capture_complete"])
   self.assertTrue(any(x["axis_a_opposition"] for x in r["candidates"]))
   self.assertFalse(r["world_axes_validated"])
if __name__=="__main__":unittest.main()
