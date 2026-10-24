import csv
import tempfile
import unittest
from pathlib import Path
from tools.analyze_spatial_position_v2_0 import (
    PHASES, ADDRS, audit, f32be, run, validate
)

class SpatialV20Tests(unittest.TestCase):
    def test_float_big_endian(self):
        self.assertEqual(f32be("42C80000"), 100.0)
        self.assertEqual(f32be("C1200000"), -10.0)

    def test_transitions_and_synchrony(self):
        markers=list(range(10,110,10))
        frames={8:{ADDRS[0]:"42C80000",ADDRS[1]:"42C80000"},
                9:{ADDRS[0]:"42C80000",ADDRS[1]:"42C80000"}}
        for idx,phase in enumerate(PHASES):
            for f in range(markers[idx],markers[idx+1]):
                change=(f==markers[idx]+1)
                frames[f]={ADDRS[0]:"42CA0000" if change else "42C80000",
                           ADDRS[1]:"42CA0000" if change else "42C80000"}
        stats,events,pairs,raw=audit("test",frames,markers)
        self.assertEqual(len(stats),len(PHASES)*2)
        self.assertEqual(pairs[0]["both_changed"],2)
        self.assertEqual(pairs[0]["only_d8_changed"],0)
        self.assertEqual(len(events),len(PHASES)*4)
        self.assertEqual(stats[0]["longest_constant_frames"],8)
        self.assertGreater(len(raw),0)

    def test_complete_session_and_prestart(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);folder=root/"output/csv";folder.mkdir(parents=True)
            sid="test";stem="spatial_v1_9_"+sid
            def write(name,fields,rows):
                with (folder/(stem+name)).open("w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=fields)
                    w.writeheader();w.writerows(rows)
            marker_frames=list(range(10,110,10))
            write("_termination.csv",["reason"],[{"reason":"stop"}])
            write("_discontinuities.csv",["previous_frame","frame"],[])
            write("_markers.csv",["frame","label"],
                  [{"frame":f,"label":label} for f,label in zip(marker_frames,PHASES+("STOP",))])
            rows=[]
            for frame in range(8,100):
                phase="PRESTART" if frame<10 else PHASES[(frame-10)//10]
                for addr in ADDRS:
                    rows.append(dict(session=sid,frame=frame,phase=phase,
                                     address=addr,raw_be="42C80000",be_float32="100"))
            write("_samples.csv",["session","frame","phase","address","raw_be","be_float32"],rows)
            paths,reports=run(sid,root)
            self.assertEqual(len(paths),4)
            self.assertEqual(reports[0][0]["first_frame"],10)
            with self.assertRaises(FileExistsError):
                run(sid,root)
            rows[0]["phase"]="FORWARD"
            write("_samples_bad.csv",["session","frame","phase","address","raw_be","be_float32"],rows)
            (folder/(stem+"_samples.csv")).unlink()
            (folder/(stem+"_samples_bad.csv")).rename(folder/(stem+"_samples.csv"))
            with self.assertRaises(ValueError):
                validate(sid,root)

if __name__=="__main__":
    unittest.main()
