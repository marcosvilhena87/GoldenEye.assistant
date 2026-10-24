import unittest
from tools.analyze_horizontal_v1_6_1 import audit, phase_comparison, OFFSETS
from tools.send_horizontal_v1_6_1 import ACTIONS, LABELS

class StationaryTargetV161Tests(unittest.TestCase):
    def fixture(self):
        sid="synthetic"
        markers=[dict(session=sid,sample_index=str(i),frame=str(i+100),label=lab)
            for i,lab in [(1,"BEGIN_MANUAL_ALIGNMENT"),(3,"END_MANUAL_ALIGNMENT"),
                          (5,"BEGIN_STATIONARY_TARGET"),(7,"END_STATIONARY_TARGET")]]
        timeline=[]
        for i in range(1,8):
            for o in OFFSETS:
                val="00000000"
                if o=="0x0D3D40":val="C0000000"
                if o=="0x0D3998" and i>=2:val="3F800000"
                if o=="0x0D3D40" and i>=2:val="BF800000"
                timeline.append(dict(session=sid,sample_index=str(i),frame=str(i+100),
                    offset_hex=o,raw_hex=val))
        return sid,markers,timeline
    def test_markers_supported(self):
        for action in ("MANUAL_ALIGNMENT","STATIONARY_TARGET","STATIONARY_TARGET_AIM_OFF"):
            self.assertIn(action,ACTIONS)
            self.assertIn("BEGIN_"+action,LABELS)
    def test_phase_audit(self):
        sid,markers,timeline=self.fixture()
        termination=[dict(session=sid,reason="stop",active_action="NONE")]
        rows,pairs=audit(markers,timeline,sid,termination,[])
        phases=phase_comparison(rows)
        self.assertEqual(len(rows),16)
        self.assertEqual(len(pairs),2)
        self.assertEqual(len(phases),8)
        self.assertEqual(phases[0]["unsupervised_gap_samples"],1)
    def test_discontinuous_rejected(self):
        sid,markers,timeline=self.fixture()
        timeline[0]["frame"]="999"
        with self.assertRaises(ValueError):
            audit(markers,timeline,sid,[dict(session=sid,reason="stop",active_action="NONE")],[])
    def test_incomplete_rejected(self):
        sid,markers,timeline=self.fixture()
        with self.assertRaises(ValueError):
            audit(markers[:-1],timeline,sid,[dict(session=sid,reason="stop",active_action="NONE")],[])

if __name__=="__main__":
    unittest.main()
