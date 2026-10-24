import unittest,struct
from tools.analyze_enemy_freeze_v1_8 import numeric,clusters,SIZE

class FullRamTests(unittest.TestCase):
    def samples(self):
        vals=[10.,20.,30.]
        blobs={}
        for e,v in enumerate(vals,1):
            d=bytearray(SIZE)
            for off in (0x100,0x104,0x108):
                d[off:off+4]=struct.pack(">f",v+off/4)
            blobs[(e,"stable")]=bytes(d)
            blobs[(e,"hold")]=bytes(d)
        blobs[(3,"camera")]=blobs[(3,"stable")]
        return blobs
    def test_numeric_and_nearby_groups(self):
        rows,stats=numeric(self.samples(),0x100,0x110)
        selected=[r for r in rows if r["format"]=="float32_be"]
        self.assertEqual(len(selected),3)
        group=clusters(selected)
        self.assertTrue(any(r["spacing"]==4 for r in group))
        self.assertTrue(all(r["review_priority"]=="review" for r in selected))
    def test_camera_soft_flag(self):
        blobs=self.samples()
        cam=bytearray(blobs[(3,"camera")]);cam[0x100:0x104]=struct.pack(">f",90)
        blobs[(3,"camera")]=bytes(cam)
        rows,_=numeric(blobs,0x100,0x104)
        self.assertTrue(any(r["camera_changed"]==1 for r in rows))
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError):numeric({},0x100,0x104)
if __name__=="__main__":unittest.main()
