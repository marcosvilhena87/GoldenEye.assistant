import tempfile
import unittest
from pathlib import Path
from tools.send_bond_soldier_v1_8_2 import send

class SenderTests(unittest.TestCase):
    def test_sequential_no_overwrite_and_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"sessions").mkdir()
            (root/"sessions/bond_soldier_v1_8_2_session.txt").write_text("example_123\n")
            first=send("BASELINE",root)
            second=send("STOP",root)
            self.assertEqual(first.name,"bond_soldier_v1_8_2_example_123_0001.txt")
            self.assertEqual(second.name,"bond_soldier_v1_8_2_example_123_0002.txt")
            self.assertEqual(first.read_text(),"LABEL:BASELINE\n")
            self.assertEqual(second.read_text(),"LABEL:STOP\n")
    def test_invalid_label(self):
        with self.assertRaises(ValueError):
            send("TARGET_EC")
if __name__=="__main__":
    unittest.main()
