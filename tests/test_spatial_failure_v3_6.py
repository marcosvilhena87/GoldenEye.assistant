import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze_spatial_failure_v3_6 import (
    classify, diagnose, read_v35, run, REQUIRED
)

SESSION_A = "a"
SESSION_B = "b"
OFFSET = "0x3B30E0"
KIND = "be_f32"


def record(session, *, movement=1, reverse=1, ret=1, rot=1, stable=1):
    passed = movement and reverse and ret and rot and stable
    row = dict(session=session, offset=OFFSET, kind=KIND,
               second_step_nonzero=str(movement),
               direction_reversed=str(reverse), return_close=str(ret),
               rotation_unchanged=str(rot), holds_stable=str(stable),
               candidate=str(int(bool(passed))))
    for key in ("step1", "back", "step2", "return_error_ratio",
                "rotation_error_ratio", "max_hold_mad_ratio", "p0", "p1",
                "p0_return", "p0_rotated", "p2"):
        row[key] = "0.0"
    row.update(step1="5.0", back="-5.0", step2="8.0")
    return row


class SpatialFailureV36Tests(unittest.TestCase):
    def test_per_criterion_and_conjunction(self):
        row = classify(record("a", reverse=0, stable=0), "a", OFFSET, KIND)
        self.assertEqual(row["failed_count"], 2)
        self.assertEqual(row["failed_criteria"], "direction_reversed;holds_stable")
        self.assertEqual(row["v36_all_pass"], 0)

    def test_missing_not_inferred_as_failure_of_physics(self):
        rows, cross, summary = diagnose({("a", OFFSET, KIND): record("a")},
                                        ("a", "b"))
        self.assertEqual(len(rows), 160)
        self.assertEqual(len(cross), 80)
        self.assertEqual(summary["evaluated_total"], 1)
        self.assertEqual(summary["missing_total"], 159)
        group = next(r for r in cross if r["offset"] == OFFSET and r["kind"] == KIND)
        self.assertEqual(group["passing_sessions"], 1)
        self.assertEqual(group["decision"], "not_supported")
        missing = next(r for r in rows if r["session"] == "b" and
                       r["offset"] == OFFSET and r["kind"] == KIND)
        self.assertEqual(missing["failed_criteria"], "missing_v35_row")

    def test_reject_duplicate_and_invalid_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            with path.open("w", newline="") as fp:
                w = csv.DictWriter(fp, fieldnames=REQUIRED)
                w.writeheader()
                w.writerow(record("a"))
                w.writerow(record("a"))
            with self.assertRaises(ValueError):
                read_v35(path, {"a", "b"})
        with self.assertRaises(ValueError):
            classify(record("a", reverse=2), "a", OFFSET, KIND)
        with self.assertRaises(ValueError):
            classify({**record("a"), "candidate": "0"}, "a", OFFSET, KIND)

    def test_write_immutable_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "output" / "csv"
            folder.mkdir(parents=True)
            path = folder / "spatial_v3_5_a__b_hold_differentials.csv"
            with path.open("w", newline="") as fp:
                w = csv.DictWriter(fp, fieldnames=REQUIRED)
                w.writeheader()
                w.writerow(record("a"))
                w.writerow(record("b", movement=0, reverse=0))
            paths, summary = run(("a", "b"), Path(tmp))
            self.assertTrue(all(p.exists() for p in paths))
            self.assertEqual(summary["cross_session_all_pass"], 0)
            with self.assertRaises(FileExistsError):
                run(("a", "b"), Path(tmp))


if __name__ == "__main__":
    unittest.main()
