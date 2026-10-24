import unittest
from tools.analyze_spatial_region_v3_1 import audit, BLOCKS, PAIRS
from tools.analyze_spatial_position_v2_4 import START, END

class RegionalV31Tests(unittest.TestCase):
    def sample(self, shift=0):
        markers=[100+i*24 for i in range(10)]
        frames={}
        for f in range(markers[0],markers[-1]):
            row={address:0 for address in range(START,END+1)}
            for j,base in enumerate(BLOCKS):
                row[base]=((f//(3+(j%4)))+shift+(j%3))%5
            row[0x3B30D0]=(f//3+shift)%5
            row[0x3B30E0]=(f//3+shift)%5
            frames[f]=row
        return frames,markers

    def test_coverage_and_replication(self):
        first,m1=self.sample(0)
        second,m2=self.sample(1)
        details,summaries,components=audit("one","two",first,m1,second,m2)
        self.assertEqual(len(BLOCKS),20)
        self.assertEqual(len(PAIRS),190)
        self.assertEqual(len(details),1710)
        self.assertEqual(len(summaries),190)
        self.assertEqual(len(components),20)
        self.assertTrue(any(x["left"]=="0x3B30D0" and x["right"]=="0x3B30E0" for x in summaries))

    def test_independence(self):
        f,m=self.sample()
        with self.assertRaises(ValueError):
            audit("same","same",f,m,f,m)

    def test_thresholds(self):
        f,m=self.sample()
        with self.assertRaises(ValueError):
            audit("a","b",f,m,f,m,threshold_sync=2)
        with self.assertRaises(ValueError):
            audit("a","b",f,m,f,m,min_phases=10)

if __name__=="__main__":
    unittest.main()
