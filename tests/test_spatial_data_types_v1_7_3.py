import struct
import unittest
from tools.validate_spatial_data_types_v1_7_3 import interpret,audit_four,count_changed,float_kind

class DataTypesTests(unittest.TestCase):
 def test_endian_int_float(self):
  raw=struct.pack("<f",2.015625)
  d=interpret(raw)
  self.assertEqual(d["float_le"],2.015625)
  self.assertEqual(d["float_le_kind"],"normal")
  self.assertEqual(d["uint32_be"],int.from_bytes(raw,"big"))
 def test_subnormal_detection(self):
  raw=bytes.fromhex("00000001")
  self.assertEqual(float_kind(raw,"big"),"subnormal")
  self.assertEqual(float_kind(raw,"little"),"normal")
 def test_nonfinite(self):
  d=interpret(bytes.fromhex("7F800000"))
  self.assertIsNone(d["float_be"])
  self.assertEqual(d["float_be_kind"],"infinity")
 def test_raw_rotation_not_mistaken_for_stable(self):
  a=bytes.fromhex("00000140")
  b=bytes.fromhex("002D5A10")
  rot=bytes.fromhex("06C00440")
  result=audit_four([a,b,a,rot],"test",0x2EC5D4)
  self.assertFalse(result["raw_rotation_equal"])
  self.assertEqual(result["classification"],"raw_rotation_sensitive_or_inconclusive")
 def test_raw_return(self):
  a=struct.pack(">f",100)
  b=struct.pack(">f",105)
  res=audit_four([a,b,a,a],"test",0x100)
  self.assertEqual(res["classification"],"raw_motion_association_unverified")
 def test_changed_bytes(self):
  self.assertEqual(count_changed(bytes.fromhex("11223344"),bytes.fromhex("11224455")),2)
 def test_invalid_length(self):
  with self.assertRaises(ValueError):interpret(b"abc")

if __name__=="__main__":unittest.main()
