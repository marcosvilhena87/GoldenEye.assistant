import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_bond_soldier_v1_8_4 import analyze,episodes,FIELDS

class FreezeTimingTests(unittest.TestCase):
    def test_episode_splitting(self):
        self.assertEqual(len(episodes([10,12,14,40,42],12)),2)
    def test_indicator_and_motion_not_promoted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sid="synthetic";base=root/("bond_soldier_v1_8_4_"+sid)
            with Path(str(base)+"_timeline.csv").open("w",newline="") as out:
                w=csv.writer(out)
                w.writerow(["session","frame","phase","field","offset_hex","kseg0_hex","kseg1_hex","float32_be","alias_equal","changed"])
                for n in range(400):
                    phase="FREEZE_ON" if n<200 else "SOLDIER_MOVING"
                    for f in FIELDS:
                        v="00000000"
                        if f=="freeze_indicator_candidate":v="FF" if n<200 else "00"
                        if f in ("soldier_1_a","soldier_1_b") and 210<=n<240:v=f"{n:08X}"
                        w.writerow([sid,n,phase,f,"0x00",v,v,"0",1,0])
            Path(str(base)+"_markers.csv").write_text("session,frame,label\nsynthetic,0,FREEZE_ON\nsynthetic,200,SOLDIER_MOVING\n")
            Path(str(base)+"_termination.csv").write_text("session,frame,reason\nsynthetic,400,stop\n")
            report=analyze(sid,root)
            self.assertTrue(report["capture_complete"])
            self.assertGreater(len(report["joint_soldier_episodes"]),0)
            self.assertEqual(len(report["freeze_indicator_transitions"]),1)
            self.assertFalse(report["soldier_coordinate_validated"])
            self.assertFalse(report["freeze_indicator_validated"])
if __name__=="__main__":unittest.main()
