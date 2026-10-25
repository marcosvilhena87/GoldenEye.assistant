import csv
import math
import struct
import tempfile
import unittest
from pathlib import Path

from tools.analyze_soldier_dual_axis_v1_8_9 import analyze


class DualAxisTests(unittest.TestCase):
    def write_fixture(self, folder, sid="synthetic"):
        path = Path(folder) / f"soldier_chase_v1_8_8_1_{sid}_timeline.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(("session", "frame", "phase", "offset_hex", "raw_be", "changed"))
            for frame in range(120):
                phase = "BOND_APPROACH" if frame < 60 else "BOND_RETREAT"
                progress = frame if frame < 60 else 119 - frame
                # Both hypothetical components approach (100, 200), then retreat.
                bond_a = float(progress)
                bond_b = float(progress * 2)
                fields = {
                    0x06D248: bond_a, 0x06D250: bond_b,
                    0x0D33EC: bond_a, 0x0D33F4: bond_b,
                    0x20F594: 100.0, 0x20F5AC: 200.0,
                    0x20F578: 100.0, 0x20F580: 200.0,
                    0x06A120: 100.0, 0x06A128: 200.0,
                }
                for offset, value in fields.items():
                    raw = struct.pack(">f", value).hex().upper()
                    writer.writerow((sid, frame, phase, f"0x{offset:06X}", raw, 0))
        return path

    def test_simultaneous_distance_and_retreat(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write_fixture(folder)
            report = analyze("synthetic", Path(folder), min_frames=30)
            self.assertEqual(report["frames"], 120)
            self.assertFalse(report["distance_is_physical_validated"])
            self.assertEqual(len(report["configs"]), 4)
            for config in report["configs"]:
                self.assertTrue(config["approach_converged"])
                self.assertTrue(config["retreat_diverged"])
                near = config["phase_metrics"]["BOND_APPROACH"]
                self.assertEqual(near["minimum_frame"], 59)
                self.assertTrue(math.isclose(
                    near["minimum_distance"], math.hypot(41.0, 82.0)))

    def test_reject_missing_phases(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write_fixture(folder)
            report = analyze("synthetic", Path(folder), min_frames=90)
            for config in report["configs"]:
                self.assertFalse(config["both_phases_available"])
                self.assertFalse(config["approach_converged"])

    def test_invalid_sid(self):
        with self.assertRaises(ValueError):
            analyze("../private")


if __name__ == "__main__":
    unittest.main()
