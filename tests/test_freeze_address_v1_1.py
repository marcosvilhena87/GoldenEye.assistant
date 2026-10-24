import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_freeze_address_v1_1 import analyze

class FreezeTransitionAnalysisTests(unittest.TestCase):
    def test_agreement_transitions_and_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            t=root/"timeline.csv";e=root/"events.csv";x=root/"termination.csv"
            with t.open("w",newline="") as f:
                w=csv.writer(f)
                w.writerow(["session","frame","candidate","address_hex","read_ok","value_u8","state"])
                for frame,a,b in [(10,0,0),(11,0,255),(12,255,255),(13,255,255)]:
                    for name,value in [("kseg0_alias",a),("kseg1_alias",b)]:
                        w.writerow(["test",frame,name,"0x00000000",1,value,"ON" if value else "OFF"])
            with e.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["session","frame","event","from_state","to_state","run_start_frame","run_frames","kseg0_u8","kseg1_u8","details"])
                w.writerow(["test",13,"TRANSITION_CONFIRMED","OFF","ON",12,2,255,255,""])
            x.write_text("session,frame,reason,frames,read_errors,alias_mismatches\ntest,13,stop,13,0,1\n")
            result=analyze(t,e,x)
            self.assertEqual(result["frames"],4)
            self.assertEqual(result["mismatched_or_unknown_frames"],1)
            self.assertEqual(result["first_mismatch_frames"],[11])
            self.assertEqual(result["agreed_states"],{"OFF":1,"ON":2})
            self.assertEqual(result["transitions"][0]["first_observed_frame"],12)
            self.assertEqual(result["transitions"][0]["confirmation_delay_frames"],1)
    def test_reject_duplicate_samples(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);t=root/"t.csv";e=root/"e.csv";x=root/"x.csv"
            t.write_text("session,frame,candidate,address_hex,read_ok,value_u8,state\ns,1,kseg0_alias,x,1,0,OFF\ns,1,kseg0_alias,x,1,0,OFF\n")
            e.write_text("session,frame,event,from_state,to_state,run_start_frame,run_frames,kseg0_u8,kseg1_u8,details\n")
            x.write_text("session,frame,reason,frames,read_errors,alias_mismatches\n")
            with self.assertRaises(ValueError):analyze(t,e,x)
if __name__=="__main__":unittest.main()
