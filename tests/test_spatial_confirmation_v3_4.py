import unittest
from tools.analyze_spatial_confirmation_v3_4 import score, PROTOCOL, digest
from tests.test_spatial_region_v3_1 import RegionalV31Tests
from tools.analyze_spatial_region_v3_1 import BLOCKS
from tools.analyze_spatial_position_v2_4 import START, END

def fixture(shift=0):
    markers=[100+i*130 for i in range(10)]
    frames={}
    for frame in range(markers[0],markers[-1]):
        row={address:0 for address in range(START,END+1)}
        for j,base in enumerate(BLOCKS):
            row[base]=(frame//(3+j%4)+shift)%7
        frames[frame]=row
    return frames,markers

class ConfirmationV34Tests(unittest.TestCase):
    def test_protocol_determinism(self):
        self.assertEqual(len(digest()),64)
        self.assertEqual(digest(),digest())
        self.assertEqual(len(PROTOCOL["pairs"]),4)

    def test_frozen_third_capture(self):
        a,m=fixture()
        b,n=fixture(3)
        phase,summary=score(PROTOCOL["discovery_session"],"session_three",a,m,b,n)
        self.assertEqual(len(phase),36)
        self.assertEqual(len(summary),4)
        self.assertEqual(sum(x["pair_role"]=="primary" for x in summary),1)
        self.assertTrue(all(x["null_trials"]==99 for x in phase))

    def test_guardrails(self):
        a,m=fixture()
        with self.assertRaises(ValueError):
            score(PROTOCOL["discovery_session"],PROTOCOL["replication_session"],a,m,a,m)
        with self.assertRaises(ValueError):
            score("wrong","new",a,m,a,m)
        with self.assertRaises(ValueError):
            score(PROTOCOL["discovery_session"],"new",a,m,a,m,trials=10)
        with self.assertRaises(ValueError):
            score(PROTOCOL["discovery_session"],"new",a,m,a,[100+i*12 for i in range(10)])

if __name__=="__main__":
    unittest.main()
