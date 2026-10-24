import unittest
from tools.validate_spatial_coordinates_v1_7_2 import analyze,strict,INPUT_FIELDS

def item(offset,dl,dr,rl=0,rr=0,el=0,er=0):
    row={x:"" for x in INPUT_FIELDS}
    row.update(offset_hex=f"0x{offset:06X}",endianness="big",
      delta_left=str(dl),delta_right=str(dr),
      rotation_delta_left=str(rl),rotation_delta_right=str(rr),
      return_error_left=str(el),return_error_right=str(er),
      left_pass="True",right_pass="True",classification="opposite_sign_unverified")
    return row

class Tests(unittest.TestCase):
    def test_absolute_tolerance_false_positive(self):
        ok,ratio,_,reason=strict(.00052,.00052,.00048)
        self.assertFalse(ok)
        self.assertEqual(reason,"below_min_movement")
        self.assertAlmostEqual(ratio,1)
    def test_strict_opposite(self):
        rows,groups,patterns=analyze([item(0x100,2,-3),item(0x104,4,-5)])
        self.assertEqual(sum(r["opposite_strict"] for r in rows),2)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]["members"],2)
    def test_equal_numeric_pattern(self):
        rows,groups,patterns=analyze([item(0x100,2,-3),item(0x200,2,-3)])
        self.assertEqual(len(patterns),1)
        self.assertEqual(patterns[0]["count"],2)
        self.assertEqual(groups,[])
    def test_relative_rotation_rejected(self):
        self.assertEqual(strict(1,.25,0)[3],"rotation_ratio_exceeded")
    def test_return_error_rejected(self):
        self.assertEqual(strict(1,0,.25)[3],"return_ratio_exceeded")
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):analyze([item(0x100,2,-3),item(0x100,2,-3)])
    def test_invalid_raw_rejected(self):
        with self.assertRaises(ValueError):analyze([item(0x101,2,-3)])

if __name__=="__main__":unittest.main()
