import csv
import struct
import tempfile
import unittest
from pathlib import Path
from tools.analyze_enemy_freeze_v1 import inspect

class SnapshotAnalyzerTests(unittest.TestCase):
    def write_manifest(self,root,rows):
        path=root/"manifest.csv"
        with path.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["session","frame","frame_after","epoch","phase","state","start_offset","bytes","file","notes"])
            w.writeheader()
            for row in rows:w.writerow(row)
        return path
    def test_two_stable_on_epochs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            names=["a.bin","b.bin","c.bin","d.bin"]
            for i,name in enumerate(names):
                data=bytearray(8388608)
                struct.pack_into(">f",data,128,12.5 if i<2 else 17.5)
                (root/name).write_bytes(data)
            rows=[]
            for i,(name,epoch,phase) in enumerate(zip(names,[2,2,4,4],["on_stable","on_hold"]*2)):
                rows.append(dict(session="test",frame=str(100+i*120),
                    frame_after=str(100+i*120),epoch=str(epoch),phase=phase,
                    state="ON",start_offset="0x000000",bytes="8388608",
                    file=name,notes="raw_bus_kseg0_unvalidated"))
            result=inspect(self.write_manifest(root,rows),root)
            self.assertEqual(result["status"],"candidate_only")
            self.assertTrue(any(r["offset_hex"]=="0x000080" and r["encoding"]=="float32_big" for r in result["candidates_first"]))
    def test_fails_nonatomic_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rows=[dict(session="test",frame="10",frame_after="11",epoch="1",
                phase="on_stable",state="ON",start_offset="0x000000",bytes="8388608",
                file="a.bin",notes="frame_changed_during_dump")]
            with self.assertRaises(ValueError):
                inspect(self.write_manifest(root,rows),root)
    def test_insufficient_epochs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertEqual(inspect(self.write_manifest(root,[]),root)["status"],"insufficient_data")

if __name__=="__main__":unittest.main()
