import csv
import struct
import tempfile
import unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_9 import audit
from tools.send_bond_heading_hud_v1_9_9 import send

class TemporalAuditTests(unittest.TestCase):
 def test_transients_and_pair_matching(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);base=root/"bond_heading_hud_v1_9_9_test"
   header=("session,frame,phase,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,"
           "angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,"
           "step_deg,reset_reason,aux_0D3998,aux_0D3D40,aux_0D39A0,aux_0D3D48,"
           "auxf_0D3998,auxf_0D3D40,auxf_0D39A0,auxf_0D3D48").split(",")
   with Path(str(base)+"_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(header)
    for i in range(8):
     phase="BASELINE_STILL" if i<3 else "CAMERA_PITCH_UP"
     value=[0,0,0,0,1,2,1,0][i]
     raw=struct.pack(">f",float(value)).hex().upper()
     w.writerow(["test",i,phase,1,0,"3F800000","00000000",1,0,1,1,0,0,0,0,0,0,0,"",
                 "00000000","00000000",raw,raw,0,0,value,value])
   Path(str(base)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\ntest,0,1,REFERENCE,0,0,0\ntest,8,2,STOP,0,0,0\n")
   Path(str(base)+"_termination.csv").write_text("session,frame,reason\ntest,8,stop\n")
   r=audit("test",root)
   self.assertTrue(r["complete"])
   sig=r["segments"][1]["signals"]["0D39A0"]
   self.assertEqual(sig["raw_change_count"],4)
   self.assertTrue(sig["returned_to_start"])
   self.assertEqual(sig["range"],2)
   self.assertEqual(r["segments"][1]["pairs"]["0D39A0_0D3D48"]["identical_raw_fraction"],1.0)
 def test_old_capture_supported(self):
  with self.assertRaises(FileNotFoundError):
   audit("missing",Path("/absent"),"v1_9_8")
 def test_sender(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"sessions").mkdir()
   (p/"sessions/bond_heading_hud_v1_9_9_session.txt").write_text("session\n")
   self.assertEqual(send("CAMERA_PITCH_UP",p).read_text(),"CAMERA_PITCH_UP\n")
if __name__=="__main__":unittest.main()
