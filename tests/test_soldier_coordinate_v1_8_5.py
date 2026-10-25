import struct
import unittest
from tools.analyze_soldier_coordinate_v1_8_5 import scan
class CandidateTests(unittest.TestCase):
    def test_candidate_follows_soldier_not_rotation(self):
        arrays=[bytearray(64) for _ in range(5)]
        for a in arrays:struct.pack_into(">f",a,8,2000.0)
        struct.pack_into(">f",arrays[3],8,2020.0)
        struct.pack_into(">f",arrays[4],8,2020.0)
        result=scan(dict(zip(("BASELINE","BOND_ROTATE","BOND_MOVE","SOLDIER_MOVE","SOLDIER_FREEZE"),map(bytes,arrays))),10)
        self.assertEqual(result["top_candidates"][0]["offset_hex"],"0x000008")
        self.assertFalse(result["top_candidates"][0]["numeric_proximity_filter"])
    def test_missing_phases(self):
        with self.assertRaises(ValueError):scan({})
if __name__=="__main__":unittest.main()
