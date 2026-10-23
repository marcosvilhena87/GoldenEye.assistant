import tempfile,unittest,csv
from pathlib import Path
from tools.analyze_autoaim_mem_v1_4 import summarize
from tools.send_autoaim_mem_v1_4 import send
class TemporalTests(unittest.TestCase):
    def test_summary_counts(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)/"timeline.csv";m=Path(d)/"marks.csv"
            t.write_text("session,frame,offset_hex,byte,changed\ns1,1,0x040A93,1,0\ns1,2,0x040A93,0,1\n")
            m.write_text("session,frame,label\ns1,2,BASE_OFF\n")
            rows,marks=summarize(t,m)
            self.assertEqual(rows[0]["changes"],1)
            self.assertEqual(len(marks),1)
    def test_atomic_marker(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for item in ["output/sessions","output/commands"]:(p/item).mkdir(parents=True)
            (p/"output/sessions/autoaim_mem_v1_4_session.txt").write_text("s1\n")
            command=send("BASE_ON",p)
            self.assertEqual(command.read_text(),"SESSION:s1\nLABEL:BASE_ON\n")
            self.assertFalse(command.with_suffix(".txt.pending").exists())
