import unittest
from tools.analyze_horizontal_v1_6 import audit
from tools.analyze_horizontal_v1_5_1 import OFFSETS

class DiscoveryV16Tests(unittest.TestCase):
    def fixture(self):
        s="trial"
        marks=[dict(session=s,sample_index="1",frame="10",label="BEGIN_FIXED_AIM_LEFT"),
               dict(session=s,sample_index="4",frame="13",label="END_FIXED_AIM_LEFT")]
        t=[]
        for i in range(4):
            for o in OFFSETS:
                v="C39BC437" if o=="0x0D3998" else "C39CC437" if o=="0x0D3D40" else "00000000"
                if i>1 and o=="0x0D3998":v="C39BCB2A"
                if i>1 and o=="0x0D3D40":v="C39CCB2A"
                t.append(dict(session=s,sample_index=str(i+1),frame=str(i+10),offset_hex=o,raw_hex=v))
        term=[dict(session=s,reason="stop",active_action="NONE")]
        return marks,t,s,term
    def test_absolute_and_pair_all_samples(self):
        m,t,s,term=self.fixture()
        rows,pairs=audit(m,t,s,term,[])
        self.assertEqual(len(rows),len(OFFSETS))
        self.assertEqual(pairs[0]["samples"],4)
        self.assertEqual(pairs[0]["paired_transitions"],1)
        self.assertEqual(pairs[0]["outliers_from_minus_two_1e4"],0)
    def test_frame_rollback_fail_closed(self):
        m,t,s,term=self.fixture()
        for row in t:
            if row["sample_index"]=="3":row["frame"]="2"
        with self.assertRaisesRegex(ValueError,"discontinuity"):
            audit(m,t,s,term,[])
    def test_incomplete_markers_fail_closed(self):
        m,t,s,term=self.fixture()
        with self.assertRaisesRegex(ValueError,"incomplete"):
            audit(m[:1],t,s,term,[])
    def test_unclosed_session_fail_closed(self):
        m,t,s,term=self.fixture()
        with self.assertRaisesRegex(ValueError,"not cleanly terminated"):
            audit(m,t,s,[],[])
    def test_discontinuity_file_fail_closed(self):
        m,t,s,term=self.fixture()
        with self.assertRaisesRegex(ValueError,"discontinuity"):
            audit(m,t,s,term,[{"session":s}])

if __name__=="__main__":
    unittest.main()
