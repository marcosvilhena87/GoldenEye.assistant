import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from tools.export_mapping import export, lua

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "catalog").mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test",
                        "-c", "user.email=test@example.org", "commit", "-q", "--allow-empty", "-m", "test"], check=True)
        self.write("roms", [{"id": "usa", "sha256": "a"*64, "region": "USA", "revision": "0", "format": "n64"}])
        self.write("symbols", [])

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, value):
        (self.root / "catalog" / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")

    def test_empty_is_safe(self):
        r = export(self.root, "usa")
        self.assertEqual(r["symbols"], [])
        self.assertEqual(r["sha256"], "a"*64)
        self.assertEqual(len(r["mapping_commit"]), 40)

    def test_wrong_rom_rejected(self):
        with self.assertRaises(ValueError):
            export(self.root, "unknown")

    def test_duplicate_symbols_rejected(self):
        s = {"id": "player", "rom_id": "usa", "status": "candidate"}
        self.write("symbols", [s, s])
        with self.assertRaises(ValueError):
            export(self.root, "usa")

    def test_lua_escapes(self):
        self.assertIn("\\034", lua('"'))
        self.assertIn("\\092", lua("\\"))

if __name__ == "__main__":
    unittest.main()
