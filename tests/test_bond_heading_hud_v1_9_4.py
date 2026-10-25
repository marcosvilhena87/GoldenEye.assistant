import tempfile,unittest
from pathlib import Path
from tools.send_bond_heading_hud_v1_9_4 import send
class SenderTests(unittest.TestCase):
 def test_commands(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"sessions").mkdir()
   (root/"sessions/bond_heading_hud_v1_9_4_session.txt").write_text("session123\n")
   a=send("REFERENCE",root);b=send("TARGET_90",root)
   self.assertEqual(a.name,"bond_heading_hud_v1_9_4_session123_0001.txt")
   self.assertEqual(b.name,"bond_heading_hud_v1_9_4_session123_0002.txt")
   self.assertEqual(b.read_text(),"TARGET_90\n")
 def test_invalid(self):
  with self.assertRaises(ValueError):send("WRITE_RAM")
if __name__=="__main__":unittest.main()
