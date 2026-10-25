import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_bond_soldier_v1_8_2 import analyze

class CorrelationV182Tests(unittest.TestCase):
    def test_isolated_ec_change_keeps_soldier_raw_stable_but_not_axes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sid = "synthetic"
            stem = root / ("bond_soldier_v1_8_2_" + sid)
            fields = ["bond_e8","bond_ec","bond_f0","bond_f4","soldier_1_a","soldier_1_b"]
            with Path(str(stem)+"_timeline.csv").open("w",newline="") as out:
                writer=csv.writer(out)
                writer.writerow(["session","frame","phase","field","offset_hex","kseg0_hex","kseg1_hex","float32_be","alias_equal","changed"])
                for frame in range(122):
                    for field in fields:
                        val="469CCB48" if field=="bond_ec" and frame>=1 else "469DCB48"
                        writer.writerow([sid,frame,"WRITE_PRE",field,"0x000000",val,val,"20069.6406" if val=="469CCB48" else "20197.6406",1,int(frame==1 and field=="bond_ec")])
            Path(str(stem)+"_markers.csv").write_text("session,frame,label\n",encoding="utf-8")
            Path(str(stem)+"_termination.csv").write_text("session,frame,reason\nsynthetic,122,stop\n",encoding="utf-8")
            r=analyze(sid,root)
            self.assertEqual(len(r["intervention_candidates"]),1)
            self.assertTrue(r["intervention_candidates"][0]["soldier_unchanged_at_transition"])
            self.assertTrue(r["intervention_candidates"][0]["soldier_stable_next_120_frames"])
            self.assertFalse(r["physical_position_correlation_validated"])
            self.assertFalse(r["canonical_axes_validated"])

if __name__=="__main__":
    unittest.main()
