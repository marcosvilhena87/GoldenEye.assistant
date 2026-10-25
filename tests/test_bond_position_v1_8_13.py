import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_bond_position_v1_8_13 import analyze
from tools.compare_bond_position_v1_8_13 import compare
class BondPositionTests(unittest.TestCase):
 def test_reversible_position_and_frozen_soldier(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sid="demo";stem=root/f"bond_position_v1_8_13_{sid}"
   phases=["ORIGIN_STILL","ROTATE_LEFT","ROTATE_RIGHT","ORIGIN_AFTER_ROTATION",
    "MOVE_FORWARD","DESTINATION_STILL","MOVE_BACK","RETURN_STILL",
    "MOVE_FORWARD_REPEAT","DESTINATION_REPEAT_STILL","MOVE_BACK_REPEAT","RETURN_REPEAT_STILL"]
   positions=[0,0,0,0,None,100,None,0,None,100,None,0]
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for frame in range(40*len(phases)):
     p=frame//40;t=frame%40
     x=(t*100/39 if p in (4,8) else 100-t*100/39 if p in (6,10) else positions[p])
     y=x*0.5
     fields={0x06D248:x,0x0D33EC:x,0x06D250:y,0x0D33F4:y,
       0x20F594:220,0x20F5AC:120,0x20F578:220,0x20F580:120,0x06A120:220,0x06A128:120}
     for off,v in fields.items():
      w.writerow([sid,frame,phases[p],f"0x{off:06X}",struct.pack(">f",float(v)).hex().upper(),0])
   Path(str(stem)+"_markers.csv").write_text("session,frame,label\n")
   Path(str(stem)+"_termination.csv").write_text(f"session,frame,reason\n{sid},480,stop\n")
   r=analyze(sid,root)
   self.assertTrue(r["capture_complete"])
   self.assertEqual(r["results"][0]["return_error_by_phase"]["RETURN_STILL"],0)
   self.assertEqual(r["results"][0]["repeat_destination_error"],0)
   self.assertTrue(all(c["constant_across_phases"] for c in r["results"][0]["soldier_candidates"]))
   self.assertEqual(r["aliases"][0]["raw_equal_fraction"],1)
   self.assertFalse(r["physical_xyz_validated"])
   with self.assertRaises(ValueError):compare(r,r)
 def test_reject_unsafe_sid(self):
  with self.assertRaises(ValueError):analyze("../bad")
if __name__=="__main__":unittest.main()
