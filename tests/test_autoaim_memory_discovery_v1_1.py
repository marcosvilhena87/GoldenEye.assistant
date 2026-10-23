"""Synthetic regression tests for Auto-Aim Memory Discovery v1.1 analyzer."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/analyze_autoaim_mem_v1_1.py"
spec = importlib.util.spec_from_file_location("autoaim_analysis_v1_1", SCRIPT)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)

class DiscoveryAnalyzerTests(unittest.TestCase):
    def test_strict_filter_and_previous_intersection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/"output/csv").mkdir(parents=True)
            (root/"output/archive").mkdir(parents=True)
            session = "synthetic"
            labels = analysis.LABELS
            # index 0 strict / matches previous; 1 changed but ON unstable;
            # 2 changed but OFF unstable; 3 changed but negative control fails.
            snapshots = [
                bytes([1,1,1,1]),   # A1
                bytes([1,8,1,1]),   # A_STABLE
                bytes([0,0,0,0]),   # B
                bytes([0,0,9,0]),   # B_STABLE
                bytes([1,1,1,1]),   # A2
                bytes([1,1,1,9]),   # CONTROL_A
            ]
            manifest = root/"output/csv/autoaim_mem_v1_1_manifest.csv"
            with manifest.open("w",newline="",encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["session","label","frame","domain","size","path"])
                for i,(label,blob) in enumerate(zip(labels,snapshots)):
                    rel=f"output/archive/{label}.bin"
                    (root/rel).write_bytes(blob)
                    writer.writerow([session,label,i,"RDRAM",4,rel])
            prior=root/"output/csv/autoaim_mem_v1_candidates_prior.csv"
            with prior.open("w",newline="",encoding="utf-8") as f:
                w=csv.writer(f);w.writerow(["offset_hex"]);w.writerow(["0x000000"])
            with patch.object(analysis,"ROOT",root):
                counts,out=analysis.analyze(session,prior)
            self.assertEqual(counts["a1_b_changed"],4)
            self.assertEqual(counts["strict"],1)
            self.assertEqual(counts["intersect_previous"],1)
            with out.open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]["offset_hex"],"0x000000")
            self.assertEqual(rows[0]["status"],"candidate_control_filtered_only")

if __name__=="__main__":
    unittest.main()
