import tempfile
import unittest
from pathlib import Path
from tools.analyze_spatial_position_v2_1 import (
    decode,runs,lag_scores,cross_scores,audit,run,ADDRS,PHASES
)

class SpatialV21Tests(unittest.TestCase):
    def test_signed_and_endianness(self):
        v=decode("BF800000")
        self.assertEqual(v["be_f32"],-1.0)
        self.assertEqual(v["be_i32"],-1082130432)
        self.assertEqual(v["be_u16_0"],0xBF80)
        self.assertEqual(v["le_u16_0"],0x80BF)
        self.assertEqual(v["byte_0"],0xBF)

    def test_periodic_raw(self):
        a=["00000000","00000001"]*8
        result=lag_scores(a,4)
        self.assertEqual(result[1][2],1.0)
        self.assertEqual(result[0][2],0.0)
        self.assertEqual(runs(a),1)

    def test_cross_lag(self):
        a=["0","1","1","0","0","1","1","0"]*3
        b=["0"]+a[:-1]
        scores=cross_scores(a,b,3)
        self.assertEqual(next(x for x in scores if x[0]==1)[2],1.0)

    def test_audit_keeps_phases_separate(self):
        markers=list(range(10,110,10))
        data={}
        for frame in range(10,100):
            raw="3F800000" if frame%2 else "00000000"
            data[frame]={ADDRS[0]:raw,ADDRS[1]:raw}
        reports=audit("test",data,markers,max_lag=3)
        self.assertEqual(len(reports[2]),len(PHASES)*len(ADDRS)*4)
        self.assertEqual(len(reports[3]),len(PHASES)*7)
        self.assertTrue(all(x["longest_run"]>=1 for x in reports[0]))

    def test_no_overwrite(self):
        # Missing source must fail, not fabricate a session or reports.
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                run("missing",Path(temp))
if __name__=="__main__":
    unittest.main()
