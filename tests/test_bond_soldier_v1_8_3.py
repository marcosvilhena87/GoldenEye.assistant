import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_bond_soldier_v1_8_3 import analyze
from tools.send_bond_soldier_v1_8_3 import send

FIELDS=("bond_e8","bond_ec","bond_f0","bond_f4","soldier_1_a","soldier_1_b")
class PositiveControlTests(unittest.TestCase):
    def test_positive_candidate_not_xyz(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);sid="synthetic";base=root/("bond_soldier_v1_8_3_"+sid)
            phases=["FREEZE_ON"]*125+["SOLDIER_STILL"]*125+["SOLDIER_MOVING"]*125+["SOLDIER_REFROZEN"]*125
            with Path(str(base)+"_timeline.csv").open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["session","frame","phase","field","offset_hex","kseg0_hex","kseg1_hex","float32_be","alias_equal","changed"])
                for frame,phase in enumerate(phases):
                    for field in FIELDS:
                        value="469DCB48"
                        if field=="soldier_1_a" and frame>=275:value="469CCB48"
                        w.writerow([sid,frame,phase,field,"0x000000",value,value,"1.0",1,0])
            Path(str(base)+"_markers.csv").write_text("session,frame,label\n")
            Path(str(base)+"_termination.csv").write_text("session,frame,reason\nsynthetic,500,stop\n")
            result=analyze(sid,root)
            self.assertEqual(result["positive_control"]["classification"],"candidate_motion_response_observed")
            self.assertFalse(result["soldier_xyz_validated"])
    def test_sender(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);(base/"sessions").mkdir()
            (base/"sessions/bond_soldier_v1_8_3_session.txt").write_text("sample\n")
            p=send("SOLDIER_MOVING",base)
            self.assertEqual(p.read_text(),"LABEL:SOLDIER_MOVING\n")

if __name__=="__main__":unittest.main()
