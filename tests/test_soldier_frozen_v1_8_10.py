import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_frozen_v1_8_10 import analyze
class FrozenMotionTests(unittest.TestCase):
 def fixture(self,path,drifting=False):
  phases=("FROZEN_BASELINE","BOND_APPROACH","BOND_STOP_NEAR","BOND_ROTATE","BOND_RETREAT","BOND_STOP_FAR")
  with path.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(("session","frame","phase","offset_hex","raw_be","changed"))
   for n in range(240):
    phase=phases[n//20];step=n%20
    positions=((0.0,0.0),(step*2.0,step*4.0),(80.0,80.0),(80.0,80.0),(80-step*2.0,80-step*4.0),(0.0,0.0))
    ba,bb=positions[n//20]
    sx=100.0+(1.0 if drifting and n>=160 else 0.0)
    fields={0x06D248:ba,0x06D250:bb,0x0D33EC:ba,0x0D33F4:bb,
      0x20F594:sx,0x20F5AC:100.0,0x20F578:sx,0x20F580:100.0,0x06A120:sx,0x06A128:100.0}
    for off,value in fields.items():
     w.writerow(("demo",n,phase,f"0x{off:06X}",struct.pack(">f",value).hex().upper(),0))
 def run_fixture(self,d,drifting):
  root=Path(d);stem=root/"soldier_frozen_v1_8_10_demo"
  self.fixture(Path(str(stem)+"_timeline.csv"),drifting)
  Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
  Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,240,stop\n")
  return analyze("demo",root)
 def test_stable_soldier_and_bond_convergence(self):
  with tempfile.TemporaryDirectory() as d:
   report=self.run_fixture(d,False)
   self.assertTrue(report["capture_complete"])
   self.assertTrue(all(r["controlled_convergence_supported"] for r in report["results"]))
   self.assertFalse(report["physical_distance_validated"])
 def test_frozen_state_changes_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   report=self.run_fixture(d,True)
   self.assertTrue(all(not r["controlled_convergence_supported"] for r in report["results"]))
if __name__=="__main__":unittest.main()
