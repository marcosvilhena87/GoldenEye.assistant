import struct
import unittest
from tools.analyze_spatial_physical_v3_5 import (
    sample_session,summarize,paired_axes,OFFSETS,KINDS
)
from tools.analyze_spatial_position_v2_4 import START,END

class PhysicalV35Tests(unittest.TestCase):
    def fixture(self,session):
        markers=[100+i*150 for i in range(10)]
        frames={}
        # p0=1, p1=6, return=1, rotated=1, p2=9
        stages=[1,1,6,6,1,1,1,1,9]
        for i in range(9):
            for f in range(markers[i],markers[i+1]):
                row={x:0 for x in range(START,END+1)}
                v=stages[i]
                row.update(dict(zip(range(0x3B30E0,0x3B30E4),struct.pack(">f",float(v)))))
                # constant decoy
                row.update(dict(zip(range(0x3B30C0,0x3B30C4),struct.pack(">f",2.0))))
                frames[f]=row
        return frames,markers

    def test_valid_floating_position_candidate(self):
        frames,bounds=self.fixture("a")
        rows=sample_session("a",frames,bounds)
        candidate=next(r for r in rows if r["offset"]=="0x3B30E0" and r["kind"]=="be_f32")
        self.assertEqual(candidate["candidate"],1)
        self.assertEqual(candidate["step1"],5)
        decoy=next(r for r in rows if r["offset"]=="0x3B30C0" and r["kind"]=="be_f32")
        self.assertEqual(decoy["candidate"],0)

    def test_cross_session(self):
        a,m=self.fixture("a")
        x=sample_session("a",a,m)
        y=sample_session("b",a,m)
        summary=summarize([x,y])
        c=next(r for r in summary if r["offset"]=="0x3B30E0" and r["kind"]=="be_f32")
        self.assertEqual(c["decision"],"cross_session_candidate")
        self.assertEqual(c["passed"],2)
        self.assertIsInstance(paired_axes([x,y],summary),list)

    def test_reject_short_hold_and_duplicate(self):
        frames,bounds=self.fixture("a")
        with self.assertRaises(ValueError):sample_session("a",frames,bounds,tail=151)
        with self.assertRaises(ValueError):summarize([sample_session("a",frames,bounds)]*2)

if __name__=="__main__":
    unittest.main()
