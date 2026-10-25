import csv,struct,tempfile,unittest
from pathlib import Path
from tools.analyze_soldier_autoaim_v1_8_11 import analyze
class AutoAimRotationTests(unittest.TestCase):
 def test_on_off_and_frozen_fields(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sid="demo";file=root/f"soldier_autoaim_v1_8_11_{sid}_timeline.csv"
   phases=["AIM_ON_STILL","AIM_ON_ROTATE","AIM_ON_SETTLE","AIM_OFF_STILL","AIM_OFF_ROTATE","AIM_OFF_SETTLE"]
   with file.open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n in range(240):
     p=phases[n//40];t=n%40
     x=50.0+(t*0.25 if p=="AIM_ON_ROTATE" else t*0.02 if p=="AIM_OFF_ROTATE" else 0)
     values={0x06D248:x,0x06D250:70.0,0x0D33EC:x,0x0D33F4:70.0,
             0x20F594:100.0,0x20F5AC:120.0,0x20F578:100.0,0x20F580:120.0,
             0x06A120:100.0,0x06A128:120.0}
     for addr,val in values.items():
      w.writerow([sid,n,p,f"0x{addr:06X}",struct.pack(">f",val).hex().upper(),0])
   r=analyze(sid,root)
   self.assertEqual(r["frames"],240)
   self.assertGreater(r["fields"]["0x06D248"]["AIM_ON_ROTATE"]["spread"],
                      r["fields"]["0x06D248"]["AIM_OFF_ROTATE"]["spread"])
   self.assertEqual(r["fields"]["0x20F594"]["AIM_ON_ROTATE"]["spread"],0)
   self.assertFalse(r["autoaim_effect_validated"])
 def test_bad_source(self):
  with self.assertRaises(ValueError):
   analyze("demo",source="invalid")
if __name__=="__main__":unittest.main()
