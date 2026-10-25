import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_proximity_v1_8_8_2 import analyze
class ProximityTests(unittest.TestCase):
 def test_approach_and_retreat(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);file=root/"soldier_chase_v1_8_8_1_demo_timeline.csv"
   with file.open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(80):
     phase="BOND_APPROACH" if n<40 else "BOND_RETREAT"
     b=100.0+float(n if n<40 else 80-n)
     for off,value in ((0x0D33E8,b),(0x20F594,150.0)):
      w.writerow(["demo",n,phase,f"0x{off:06X}",struct.pack(">f",value).hex().upper(),1])
   report=analyze("demo",root,min_frames=20)
   found=[p for p in report["pairs"] if p["bond_offset"]=="0x0D33E8" and p["soldier_offset"]=="0x20F594" and p["float_format"]==">f"]
   self.assertEqual(len(found),1)
   self.assertTrue(found[0]["approach_converged"])
   self.assertTrue(found[0]["retreat_diverged"])
   self.assertFalse(report["physical_distance_validated"])
if __name__=="__main__":unittest.main()
