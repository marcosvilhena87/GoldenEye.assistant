import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_spatial_axes_v3_7 import audit,analyze,run,REQUIRED


def row(session, offset, x, back, z, mad=0., rotation=0., rr=0.):
    return dict(session=session,offset=offset,kind="be_f32",step1=str(x),
                back=str(back),step2=str(z),max_hold_mad_ratio=str(mad),
                return_error_ratio=str(rr),rotation_error_ratio=str(rotation),
                direction_reversed=str(int(x*back<0)),
                return_close=str(int(rr<=.1)),
                rotation_unchanged=str(int(rotation<=.1)),
                holds_stable=str(int(mad<=.02)))

class AxisV37Tests(unittest.TestCase):
    def test_first_only_and_second_only(self):
        a=audit(row("a","0x3B30B0",5,-5,0),"a","0x3B30B0","be_f32")
        b=audit(row("a","0x3B30B4",0,0,7),"a","0x3B30B4","be_f32")
        self.assertEqual((a["candidate"],a["axis_role"]),(1,"first_only"))
        self.assertEqual((b["candidate"],b["axis_role"]),(1,"second_only"))

    def test_reject_second_only_when_return_drift(self):
        r=audit(row("a","0x3B30B4",0,2,7),"a","0x3B30B4","be_f32")
        self.assertEqual(r["candidate"],0)
        self.assertIn("return_leg_drift",r["failure_reasons"])

    def test_axis_pair_and_missing(self):
        rows={}
        for s in ("a","b"):
            rows[s,"0x3B30B0","be_f32"]=row(s,"0x3B30B0",5,-5,0)
            rows[s,"0x3B30B4","be_f32"]=row(s,"0x3B30B4",0,0,7)
        detail,cross,pairs,summary=analyze(rows,("a","b"))
        self.assertEqual(summary["cross_session_candidates"],2)
        self.assertEqual(summary["two_axis_candidates"],1)
        self.assertEqual(summary["missing_rows"],156)
        self.assertEqual(len(detail),160)
        self.assertEqual(len(cross),80)

    def test_reject_rotation_and_noise(self):
        bad=audit(row("a","0x3B30B0",5,-5,0,rotation=.2),
                  "a","0x3B30B0","be_f32")
        self.assertEqual(bad["candidate"],0)
        self.assertIn("rotation",bad["failure_reasons"])
        noisy=audit(row("a","0x3B30B0",5,-5,0,mad=.2),
                    "a","0x3B30B0","be_f32")
        self.assertEqual(noisy["candidate"],0)

    def test_files_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/"output"/"csv"
            folder.mkdir(parents=True)
            p=folder/"spatial_v3_5_a__b_hold_differentials.csv"
            with p.open("w",newline="") as fp:
                writer=csv.DictWriter(fp,fieldnames=REQUIRED)
                writer.writeheader()
                for s in ("a","b"):
                    writer.writerow(row(s,"0x3B30B0",5,-5,0))
            paths,_=run(("a","b"),Path(d))
            self.assertEqual(len(paths),4)
            with self.assertRaises(FileExistsError):run(("a","b"),Path(d))

if __name__=="__main__":
    unittest.main()
