import csv,struct,tempfile,unittest
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_10 import pearson,lag_scan,audit
class CorrelationTests(unittest.TestCase):
 def test_identical_and_shifted(self):
  seq=[0.,0.,1.,2.,4.,1.,0.,0.,3.,1.,0.,0.,2.,0.,0.,0.,1.,0.,0.,0.]
  r=lag_scan(seq,seq,3)
  self.assertEqual(r["best"]["lag_frames"],0)
  self.assertAlmostEqual(r["best"]["pearson"],1)
  r=lag_scan(seq,[0.,0.]+seq[:-2],3)
  self.assertEqual(r["best"]["lag_frames"],2)
 def test_flat_is_undefined(self):
  self.assertIsNone(pearson([1.,1.,1.],[1.,2.,3.]))
  self.assertIsNone(lag_scan([0.]*20,[0.]*20,4)["best"])
 def test_read_historical(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stem=root/"bond_heading_hud_v1_9_8_demo"
   header="session,frame,phase,valid,angle_deg,step_deg,aux_0D3998,aux_0D3D40,aux_0D39A0,aux_0D3D48,auxf_0D3998,auxf_0D3D40,auxf_0D39A0,auxf_0D3D48".split(",")
   with Path(str(stem)+"_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(header)
    for i in range(24):
     n=float(i%5);raw=struct.pack(">f",n).hex().upper()
     w.writerow(["demo",i,"CAMERA_PITCH_UP","1",0,0,raw,raw,raw,raw,n,n,n,n])
   Path(str(stem)+"_events.csv").write_text("session,frame,seq,event,target_deg,reference_deg,cumulative_deg\ndemo,0,1,REFERENCE,0,0,0\ndemo,24,2,STOP,0,0,0\n")
   Path(str(stem)+"_termination.csv").write_text("session,frame,reason\ndemo,24,stop\n")
   r=audit("demo",root,"v1_9_8",4)
   self.assertTrue(r["historical_complete"])
   pair=r["vertical_interventions"][0]["pairs"]["0D39A0_0D3D48"]
   self.assertEqual(pair["raw_equal_fraction"],1)
   self.assertEqual(pair["lag_scan"]["best"]["lag_frames"],0)
if __name__=="__main__":unittest.main()
