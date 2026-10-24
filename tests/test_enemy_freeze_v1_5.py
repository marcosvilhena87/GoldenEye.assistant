import unittest
from tools.analyze_enemy_freeze_v1_5 import field_events,profile,analyze,SIZE

class FieldLayoutTests(unittest.TestCase):
    def test_aligned_words_and_repetition(self):
        start=0x0D5000
        a=bytearray(SIZE);b=bytearray(SIZE)
        for o in (start,start+0x50,start+0xA0):
            a[o:o+4]=bytes((1,2,3,4))
            b[o:o+4]=bytes((5,6,7,8))
        ev=field_events([bytes(a),bytes(a),bytes(b),bytes(b)],start,start+0xB0)
        scores,phases=profile(ev,start,strides=(0x40,0x50))
        selected=[x for x in scores if x["stride_bytes"]==0x50 and x["field_width"]==4][0]
        self.assertGreaterEqual(selected["both_changed"],2)
        self.assertGreaterEqual(selected["same_p1"],2)
        self.assertGreaterEqual(selected["same_p2"],2)
    def test_hold_instability(self):
        start=0x0D5000
        a=bytearray(SIZE);ah=bytearray(SIZE);b=bytearray(SIZE)
        a[start]=1;ah[start]=2;b[start]=3
        ev=field_events([bytes(a),bytes(ah),bytes(b),bytes(b)],start,start+8)
        word=[x for x in ev if x["width"]==4 and x["offset"]==start][0]
        self.assertFalse(word["stable"])
        self.assertTrue(word["changed"])
    def test_reject_incomplete(self):
        with self.assertRaises(ValueError):field_events([b"x"]*4)
    def test_two_regions(self):
        blobs=[bytes(SIZE)]*4
        scores,phases=analyze(blobs)
        self.assertEqual(len(scores),36)
        self.assertEqual({r["region"] for r in scores},{"A","B"})
if __name__=="__main__":unittest.main()
