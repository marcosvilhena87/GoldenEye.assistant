import unittest
from tools.analyze_enemy_freeze_v1_3 import analyze, SIZE

class MirrorDynamicTests(unittest.TestCase):
    def test_mirrored_and_independent(self):
        start=0x0D5000;shift=0x11800
        a=bytearray(SIZE);b=bytearray(SIZE)
        a[start]=1;a[start+shift]=1
        b[start]=2;b[start+shift]=2
        a[start+1]=3;a[start+1+shift]=3
        b[start+1]=4;b[start+1+shift]=5
        counts,fields,runs=analyze([bytes(a),bytes(a),bytes(b),bytes(b)],start,start+3,shift)
        self.assertEqual(counts["dynamic_stable"],2)
        self.assertEqual(counts["mirror_dynamic"],1)
        self.assertEqual(counts["independent_dynamic"],1)
        self.assertEqual(counts["both_zero"],1)
        self.assertEqual([r["class_name"] for r in fields],["mirrored","distinct"])
        self.assertEqual(len(runs),2)
    def test_unstable_hold_is_excluded(self):
        start=0x0D5000;shift=0x11800
        a=bytearray(SIZE);hold=bytearray(SIZE);b=bytearray(SIZE)
        a[start]=1;hold[start]=2;b[start]=3
        counts,fields,_=analyze([bytes(a),bytes(hold),bytes(b),bytes(b)],start,start+1,shift)
        self.assertEqual(counts["dynamic_stable"],0)
        self.assertEqual(fields,[])
    def test_invalid_input(self):
        with self.assertRaises(ValueError):analyze([b"test"])
        with self.assertRaises(ValueError):analyze([bytes(SIZE)]*4,start=SIZE-2,end=SIZE)

if __name__=="__main__":unittest.main()
