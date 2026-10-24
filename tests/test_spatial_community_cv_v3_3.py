import unittest
from tools.analyze_spatial_community_cv_v3_3 import (
    audit, empirical_p, candidate_edges, communities, BLOCKS
)
from tools.analyze_spatial_position_v2_4 import START, END

class CommunityCVV33Tests(unittest.TestCase):
    def input(self):
        # Each phase needs >=24 transitions (>=25 frames), not 24 frames.
        def sample(shift):
            markers=[100+i*48 for i in range(10)]
            frames={}
            for frame in range(markers[0],markers[-1]):
                row={address:0 for address in range(START,END+1)}
                for j,base in enumerate(BLOCKS):
                    row[base]=((frame//(3+(j%4)))+shift+(j%3))%5
                row[0x3B30D0]=(frame//3+shift)%5
                row[0x3B30E0]=(frame//3+shift)%5
                frames[frame]=row
            return frames,markers
        f,m=sample(0)
        g,n=sample(1)
        edges=[dict(left=f"0x{a:06X}",right=f"0x{b:06X}",direct="1")
               for a,b in [(BLOCKS[0],BLOCKS[1]),(BLOCKS[8],BLOCKS[12])]]
        memberships=[dict(block=f"0x{x:06X}",component=1 if i<4 else 2,
                          community=1 if i<4 else 2) for i,x in enumerate(BLOCKS)]
        return f,m,g,n,edges,memberships

    def test_holdout_and_null_shape(self):
        f,m,g,n,e,c=self.input()
        result=audit("original","replica",f,m,g,n,e,c,trials=3)
        phases,groups,nulls,pairs=result
        self.assertEqual(len(phases),2*9*2)
        self.assertEqual(len(nulls),len(phases)*3)
        self.assertEqual(len(pairs),2)
        self.assertEqual(len(groups),4)
        self.assertEqual({x["test_segment"] for x in phases},{"early","late"})

    def test_empirical_p(self):
        self.assertEqual(empirical_p(.3,[.1,.2,.4]),.5)
        self.assertEqual(empirical_p(1.0,[]),"")

    def test_bad_inputs(self):
        f,m,g,n,e,c=self.input()
        with self.assertRaises(ValueError):
            audit("same","same",f,m,g,n,e,c)
        with self.assertRaises(ValueError):
            audit("a","b",f,m,g,n,e,c,trials=2)
        with self.assertRaises(ValueError):
            communities(c[:-1])
        with self.assertRaises(ValueError):
            candidate_edges([dict(left="0x123456",right="0x3B30B4",direct="1")])

if __name__=="__main__":
    unittest.main()
