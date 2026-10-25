import csv,struct,tempfile,unittest
from pathlib import Path
from tools.audit_bond_ai_freeze_v1_8_17 import audit
class FreezeIntegrityTests(unittest.TestCase):
 def test_event_integrity_and_observation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sid="demo";stem=root/f"bond_ai_causality_v1_8_16_{sid}"
   phases=["AI_FREEZE_CONFIRMED"]*4+["DECOUPLE_MOVE"]*4+["SOLDIER_OLD_TARGET"]*4+["AI_RELEASE_REQUEST"]*4+["BOND_STILL_POST_RELEASE"]*4
   with Path(str(stem)+"_timeline.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","frame","phase","offset_hex","raw_be","changed"])
    for n,p in enumerate(phases):
     a=0 if n<12 else 50
     b=0 if n<4 else 50
     for off,value in {0x06D248:a,0x06D250:a,0x0D33EC:b,0x0D33F4:b}.items():
      w.writerow([sid,n,p,f"0x{off:06X}",struct.pack(">f",float(value)).hex().upper(),0])
   obs=root/"observations.csv"
   obs.write_text("session,frame,event,confidence,notes\ndemo,17,SOLDIER_RETARGET_VISUAL,high,changed direction\n",encoding="utf-8")
   report=audit(sid,root,obs)
   self.assertEqual(report["treatments"]["first_freeze"]["distinct_raw"],1)
   self.assertEqual(report["first_release_a_only_change"]["frame"],12)
   self.assertEqual(report["observations"][0]["frames_from_first_release_numeric_event"],5)
   self.assertFalse(report["soldier_target_causality_proven"])
 def test_reject_path(self):
  with self.assertRaises(ValueError):audit("../invalid")
if __name__=="__main__":unittest.main()
