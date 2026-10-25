import csv,tempfile,unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_7_1 import audit
from tools.send_bond_heading_hud_v1_9_7_1 import send
class SeparationTests(unittest.TestCase):
 def test_integrity_and_repeated_phases(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"bond_heading_hud_v1_9_7_1_demo"
   header="session,frame,phase,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,step_deg,reset_reason,aux_0D3998,aux_0D3D40,aux_0D39A0,aux_0D3D48".split(",")
   with Path(str(stem)+"_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(header)
    for i,p in enumerate(["BASELINE_STILL"]*3+["STRAFE_LEFT"]*3+["HOLD_STRAFE_LEFT"]*3+["STRAFE_LEFT"]*3):
     w.writerow(["demo",i,p,1,90,"00000000","00000000",1,0,1,1,i,0,0,0,0,0,0,"","00000000","C0000000","00000000","00000000"])
   Path(str(stem)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\ndemo,0,1,REFERENCE,90,0,0\ndemo,12,2,STOP,90,0,0\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,12,stop\n")
   r=audit("demo",root)
   self.assertTrue(r["complete"])
   self.assertEqual([x["phase"] for x in r["segments"]].count("STRAFE_LEFT"),2)
   self.assertFalse(r["physical_bond_heading_validated"])
 def test_sender(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/"sessions").mkdir()
   (root/"sessions/bond_heading_hud_v1_9_7_1_session.txt").write_text("foo\n")
   self.assertEqual(send("R_STICK_LEFT",root).read_text(),"R_STICK_LEFT\n")
 def test_traversal(self):
  with self.assertRaises(ValueError):audit("../bad")
if __name__=="__main__":unittest.main()
