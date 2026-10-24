import unittest
from tools.analyze_enemy_freeze_v1_2 import comparison, classify, dynamics, process, SIZE

class RepeatedStructureTests(unittest.TestCase):
    def test_comparison_and_controls(self):
        blob=bytearray(SIZE)
        shift=0x11800
        start=0x0D5000
        blob[start:start+4]=b"abcd"
        blob[start+shift:start+shift+4]=b"abXd"
        count,total=comparison(blob,blob,start,start+4,shift)
        self.assertEqual((count,total),(3,4))
    def test_temporal_categories(self):
        shift=0x11800;start=0x0D5000
        a=bytearray(SIZE)
        b=bytearray(SIZE)
        # P1 A/B equal; P2 A/B unequal at this byte.
        a[start]=7;a[start+shift]=7
        b[start]=8;b[start+shift]=9
        stats,classes,changed=dynamics(bytes(a),bytes(a),bytes(b),bytes(b),
                                       start,start+4,shift)
        self.assertEqual(classes["equal_different"],1)
        self.assertEqual(len(changed),1)
        self.assertEqual(changed[0]["stable_a"],1)
        self.assertEqual(changed[0]["stable_b"],1)
    def test_different_hold_still_detected(self):
        start=0x0D5000;shift=0x11800
        a=bytearray(SIZE);h=bytearray(SIZE)
        a[start]=3;a[start+shift]=3;h[start]=4
        b=bytearray(SIZE);b[start]=5;b[start+shift]=6
        stats,classes,changed=dynamics(bytes(a),bytes(h),bytes(b),bytes(b),
                                       start,start+4,shift)
        self.assertEqual(changed[0]["stable_a"],0)
    def test_invalid_bounds(self):
        a=bytes(16)
        with self.assertRaises(ValueError):comparison(a,a,0,12,10)

if __name__=="__main__":unittest.main()
