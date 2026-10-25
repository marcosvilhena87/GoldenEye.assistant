import csv,tempfile,unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_6 import audit,compare
from tools.send_bond_heading_hud_v1_9_6 import send
class HeadingPhysicalControlTests(unittest.TestCase):
 def test_audit_and_compare(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for sid in ("one","two"):
    p=root/f"bond_heading_hud_v1_9_6_{sid}"
    with Path(str(p)+"_samples.csv").open("w",newline="") as f:
     w=csv.writer(f);w.writerow("session,frame,phase,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,step_deg,reset_reason".split(","))
     for i in range(10):
      w.writerow([sid,i,"BASELINE_STILL" if i<5 else "BODY_TURN_LEFT",1,90,"3F800000","00000000",1,0,1,1,i,0,0,90,0,90,0,""])
    Path(str(p)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\n"+sid+",0,1,BASELINE_STILL,90,0,0\n"+sid+",10,2,STOP,90,0,0\n")
    Path(str(p)+"_termination.csv").write_text("session,frame,reason\n"+sid+",10,stop\n")
   self.assertTrue(audit("one",root)["complete"])
   self.assertEqual(len(compare(["one","two"],root)["sessions"]),2)
 def test_sender(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/"sessions").mkdir()
   (root/"sessions/bond_heading_hud_v1_9_6_session.txt").write_text("sid\n")
   self.assertEqual(send("AIM_ONLY",root).read_text(),"AIM_ONLY\n")
 def test_sid(self):
  with self.assertRaises(ValueError):audit("../bad")
if __name__=="__main__":unittest.main()
