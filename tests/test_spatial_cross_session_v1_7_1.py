import struct
import unittest
from tools.validate_spatial_cross_session_v1_7_1 import evaluate,row_at,FIELDS

class CrossSessionV171Tests(unittest.TestCase):
 def test_opposite_sign_pass(self):
  def make(a,b,r,t):
   return [struct.pack(">f",x) for x in (a,b,r,t)]
  record=row_at([make(10,15,10,10),make(10,5,10,10)],0,"big")
  self.assertTrue(record["left_pass"])
  self.assertTrue(record["right_pass"])
  self.assertTrue(record["opposite_sign"])
  self.assertEqual(record["classification"],"opposite_sign_unverified")
 def test_same_sign_is_not_coordinate_proof(self):
  a=row_at([[struct.pack(">f",x) for x in seq] for seq in
      ((10,15,10,10),(100,105,100,100))],0,"big")
  self.assertEqual(a["classification"],"same_sign_unverified")
 def test_incomplete_return_rejected(self):
  ok,_,_,_,_=evaluate((10,20,100,10))
  self.assertFalse(ok)
 def test_nonfinite_rejected(self):
  self.assertFalse(evaluate((10,None,10,10))[0])
 def test_fields_stable(self):
  self.assertIn("return_error_right",FIELDS)

if __name__=="__main__":unittest.main()
