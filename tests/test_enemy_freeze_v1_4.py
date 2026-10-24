import unittest
from tools.analyze_enemy_freeze_v1_4 import score_strides,signature,SIZE

class StrideTests(unittest.TestCase):
    def test_periodic_flags(self):
        bits=[int(i%80 in (5,6,13,14)) for i in range(800)]
        rows,phases=score_strides(bits,(64,72,80,96,128))
        table={row["stride_bytes"]:row for row in rows}
        self.assertGreater(table[80]["both_dynamic_pairs"],table[72]["both_dynamic_pairs"])
        self.assertEqual(sum(r["both_dynamic"] for r in phases if r["stride_hex"]=="0x50"),
                         table[80]["both_dynamic_pairs"])
    def test_controls_no_periodicity(self):
        rows,_=score_strides([0]*500,(64,80))
        self.assertTrue(all(r["phase_enrichment"]==0 for r in rows))
    def test_signature_stable_dynamic(self):
        a=bytearray(SIZE);b=bytearray(SIZE)
        start=0x0D5000
        a[start]=10;b[start]=11
        a[start+1]=12;b[start+1]=13
        ah=bytearray(a);ah[start+1]=22
        sig=signature([bytes(a),bytes(ah),bytes(b),bytes(b)],start,start+3)
        self.assertEqual(sig,[1,0,0])
    def test_reject_bad_size(self):
        with self.assertRaises(ValueError): signature([b"test"]*4)

if __name__=="__main__":unittest.main()
