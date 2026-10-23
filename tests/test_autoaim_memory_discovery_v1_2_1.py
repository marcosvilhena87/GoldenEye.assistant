import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "send_autoaim_mem_v1_2_1.py"
spec = importlib.util.spec_from_file_location("sender_v121", SOURCE)
sender = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sender)

class AtomicCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ("sessions", "csv", "commands"):
            (self.root / name).mkdir()
        self.session = "20261023T194744Z_99999"
        (self.root / "sessions" / "autoaim_mem_v1_2_1_session.txt").write_text(self.session + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_atomic_command_and_no_pending_file(self):
        self.assertIn("created", sender.next_request("ON1", self.root))
        command = self.root / "commands" / ("autoaim_mem_v1_2_1_" + self.session + "_01.txt")
        self.assertEqual(command.read_bytes(), ("SESSION:" + self.session + "\nSNAPSHOT:ON1\n").encode("ascii"))
        self.assertFalse(command.with_suffix(".txt.pending").exists())
        self.assertIn("already exists", sender.next_request("ON1", self.root))

    def test_sequence_and_conflict(self):
        with self.assertRaisesRegex(RuntimeError, "Expected ON1"):
            sender.next_request("OFF1", self.root)
        sender.next_request("ON1", self.root)
        with self.assertRaisesRegex(RuntimeError, "Expected ON1"):
            sender.next_request("ON_STABLE", self.root)
        command = next((self.root / "commands").glob("*.txt"))
        command.write_text("BROKEN")
        with self.assertRaisesRegex(RuntimeError, "Conflicting"):
            sender.next_request("ON1", self.root)

    def test_manifest_progression(self):
        manifest = self.root / "csv" / ("autoaim_mem_v1_2_1_manifest_" + self.session + ".csv")
        with manifest.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("session", "label", "frame", "domain", "count"))
            writer.writerow((self.session, "ON1", "1", "RDRAM", "131"))
        self.assertIn("created", sender.next_request("ON_STABLE", self.root))
        self.assertFalse((self.root / "csv" / "autoaim_mem_v1_2_manifest.csv").exists())

if __name__ == "__main__":
    unittest.main()
