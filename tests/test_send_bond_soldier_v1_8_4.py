import tempfile
import unittest
from pathlib import Path
from tools.send_bond_soldier_v1_8_4 import send

class AtomicSenderTests(unittest.TestCase):
    def test_sequential_complete_no_temp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"sessions").mkdir()
            (root/"sessions/bond_soldier_v1_8_4_session.txt").write_text("example_17\n")
            a=send("SOLDIER_MOVING",root)
            b=send("STOP",root)
            self.assertEqual(a.name,"bond_soldier_v1_8_4_example_17_0001.txt")
            self.assertEqual(b.name,"bond_soldier_v1_8_4_example_17_0002.txt")
            self.assertEqual(a.read_bytes(),b"LABEL:SOLDIER_MOVING\n")
            self.assertEqual(b.read_bytes(),b"LABEL:STOP\n")
            self.assertFalse(list((root/"commands").glob("*.tmp")))
            self.assertFalse(list((root/"commands").glob(".*.tmp")))
    def test_invalid_label(self):
        with self.assertRaises(ValueError):
            send("NOT_A_LABEL")
if __name__=="__main__":
    unittest.main()
