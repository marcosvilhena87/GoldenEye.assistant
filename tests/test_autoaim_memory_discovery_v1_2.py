"""Synthetic v1.2 watchlist and controls regression tests."""
import csv,importlib.util,tempfile,unittest
from pathlib import Path
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
prep=load("tools/prepare_autoaim_mem_v1_2.py","prep_autoaim_v12")
ana=load("tools/analyze_autoaim_mem_v1_2.py","analyze_autoaim_v12")
class V12Tests(unittest.TestCase):
 def test_watchlist_intersection(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/"output/commands").mkdir(parents=True)
   src=root/"cand.csv"
   with src.open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","domain","offset_hex","on_byte","off_byte","in_v1_candidates","status"])
    w.writerow(["abc","RDRAM","0x000023",1,0,"yes","candidate_control_filtered_only"])
    w.writerow(["abc","RDRAM","0x000024",1,0,"no","candidate_control_filtered_only"])
   output=root/"output/commands/watch.csv"
   result,meta=prep.prepare(src,output)
   self.assertEqual(meta["candidate_count"],1)
   self.assertIn("0x000023",result.read_text())
   self.assertNotIn("0x000024",result.read_text())
 def test_control_consistency(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=root/"output/csv";folder.mkdir(parents=True)
   with (folder/"autoaim_mem_v1_2_manifest.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","label","frame","domain","count"])
    for i,label in enumerate(ana.LABELS):w.writerow(["trial",label,i,"RDRAM",2])
   with (folder/"autoaim_mem_v1_2_samples.csv").open("w",newline="") as f:
    w=csv.writer(f);w.writerow(["session","label","frame","domain","offset_hex","byte"])
    for i,label in enumerate(ana.LABELS):
     for o in ["0x000023","0x000024"]:
      v=(1 if label in ana.ON else 0) if o=="0x000023" else (i%2)
      w.writerow(["trial",label,i,"RDRAM",o,v])
   res=ana.analyze("trial",root)
   self.assertEqual(res,{"consistent":1,"inconsistent":1})
if __name__=="__main__":unittest.main()
