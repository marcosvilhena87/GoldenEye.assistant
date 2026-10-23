import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_horizontal_v1_1 import candidate_locations, decode_values, FORMATS


class HorizontalV11Tests(unittest.TestCase):
    def test_type_decoder_endianness(self):
        self.assertEqual(decode_values([bytes.fromhex("0002")], ">h"), [2])
        self.assertEqual(decode_values([bytes.fromhex("0002")], "<h"), [512])
        self.assertEqual(decode_values([bytes.fromhex("3f800000")], ">f"), [1.0])

    def test_nonfinite_float_rejected(self):
        self.assertIsNone(decode_values([bytes.fromhex("7fc00000")], ">f"))

    def test_neighbor_locations(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            with path.open("w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["offset_hex"])
                w.writerow(["0x000004"])
            self.assertEqual(candidate_locations(path), [1, 2, 3, 4])

    def test_no_duplicate_candidate_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            path.write_text("offset_hex\\n0x000003\\n0x000003\\n".replace("\\n", "\n"))
            with self.assertRaises(ValueError):
                candidate_locations(path)

    def test_formats(self):
        self.assertEqual(len(FORMATS), 6)
