import csv,tempfile,unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_8 import audit
from tools.send_bond_heading_hud_v1_9_8 import send

class PitchDiscoveryTests(unittest.TestCase):
 def test_segments_and_differential(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);p=root/"bond_heading_hud_v1_9_8_synthetic"
   header="session,frame,phase,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,step_deg,reset_reason,aux_0D3998,aux_0D3D40,aux_0D39A0,aux_0D3D48,auxf_0D3998,auxf_0D3D40,auxf_0D39A0,auxf_0D3D48".split(",")
   with Path(str(p)+"_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(header)
    for i in range(12):
     phase="BASELINE_STILL" if i<4 else "CAMERA_PITCH_UP" if i<8 else "AIM_MODE_PITCH_UP"
     changed=str(i) if i>=4 else "0"
     w.writerow(["synthetic",i,phase,1,0,"3F800000","00000000",1,0,1,1,0,0,0,0,0,0,0,"",changed,changed,changed,changed,*([float(i)]*4)])
   Path(str(p)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\nsynthetic,0,1,REFERENCE,0,0,0\nsynthetic,12,2,STOP,0,0,0\n")
   Path(str(p)+"_termination.csv").write_text("session,frame,reason\nsynthetic,12,stop\n")
   r=audit("synthetic",root)
   self.assertTrue(r["complete"])
   self.assertEqual(len(r["segments"]),3)
   self.assertEqual(r["differential_raw_activity"][0]["camera_pitch_changes"],3)
   self.assertFalse(r["pitch_address_confirmed"])
 def test_sender(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/"sessions").mkdir()
   (root/"sessions/bond_heading_hud_v1_9_8_session.txt").write_text("abc\n")
   self.assertEqual(send("CAMERA_PITCH_UP",root).read_text(),"CAMERA_PITCH_UP\n")
 def test_sid_safety(self):
  with self.assertRaises(ValueError):audit("../../bad")
if __name__=="__main__":unittest.main()
