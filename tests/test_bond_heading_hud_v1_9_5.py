import csv,tempfile,unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_5 import audit
from tools.send_bond_heading_hud_v1_9_5 import send
class HUDLoggingTests(unittest.TestCase):
 def test_audit_valid(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base=root/"bond_heading_hud_v1_9_5_demo"
   head="session,frame,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,step_deg,reset_reason"
   with Path(str(base)+"_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(head.split(","))
    for n in range(10,31):
     w.writerow(["demo",n,1 if n<20 else 2,90,"3F800000","00000000",1,0,1,1,0,0,0,90,0,90,0,""])
   Path(str(base)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\ndemo,10,1,REFERENCE,90,0,0\ndemo,20,2,TARGET_90,90,0,0\ndemo,31,3,STOP,90,0,0\n")
   Path(str(base)+"_termination.csv").write_text("session,frame,reason\ndemo,31,stop\n")
   r=audit("demo",root)
   self.assertTrue(r["complete"]);self.assertEqual(r["samples"],21)
   self.assertEqual(r["acks"],2)
   self.assertEqual(r["target_intervals"][0]["valid_frames"],11)
 def test_invalid_sid(self):
  with self.assertRaises(ValueError):audit("../escape")
 def test_sender(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"sessions").mkdir()
   (root/"sessions/bond_heading_hud_v1_9_5_session.txt").write_text("abc\n")
   self.assertTrue(send("REFERENCE",root).name.endswith("0001.txt"))
if __name__=="__main__":unittest.main()
