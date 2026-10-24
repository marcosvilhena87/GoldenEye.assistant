import struct
import unittest
from tools.analyze_spatial_v1_7 import rank_snapshots

class SpatialTests(unittest.TestCase):
 def test_translational_candidate_and_rotating_distractor(self):
  def buf(x,y):
   data=bytearray(32)
   struct.pack_into(">f",data,4,x)
   struct.pack_into(">f",data,12,y)
   return bytes(data)
  base=buf(100,10)
  moved=buf(105,30)
  rotated=buf(100,45)
  returned=buf(100,10)
  rows=rank_snapshots(base,moved,rotated,returned)
  self.assertTrue(any(x["offset_hex"]=="0x000004" and x["endianness"]=="big" for x in rows))
  self.assertFalse(any(x["offset_hex"]=="0x00000C" and x["endianness"]=="big" for x in rows))
 def test_malformed_size_fails(self):
  with self.assertRaises(ValueError):
   rank_snapshots(bytes(8),bytes(12),bytes(8))
 def test_return_control_rejects_unrestored(self):
  def v(f):return struct.pack(">f",f)
  self.assertEqual(rank_snapshots(v(1),v(2),v(1),v(4)),[])

if __name__=="__main__":unittest.main()
