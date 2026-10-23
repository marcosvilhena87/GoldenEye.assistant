import tempfile
import unittest
from pathlib import Path
from tools.analyze_autoaim_mem_v1_4_1 import correlate,read_rows
def event(frame,offset,old,new):
    return dict(session="s",frame=str(frame),offset_hex=offset,old_byte=str(old),new_byte=str(new))
class CorrelationTests(unittest.TestCase):
    def test_pair_sync_and_ramp(self):
        events=[event(10,"0x0D308B",1,0),event(10,"0x0D309B",1,0)]
        events += [event(i,"0x067D37",i-20,i-19) for i in (21,22,23,24)]
        links,episodes,pair,ramps=correlate(events,[dict(session="s",frame="12",label="BASE_OFF")],window=5,gap=1)
        self.assertTrue(pair["exact_frame_sync"])
        self.assertEqual(pair["shared_frames"],1)
        self.assertEqual(links[0]["delta_frames"],-2)
        self.assertEqual(len(ramps),1)
        self.assertEqual(len(episodes),2)
    def test_no_marker_and_pair_mismatch(self):
        events=[event(2,"0x0D308B",1,0),event(3,"0x0D309B",1,0)]
        links,episodes,pair,ramps=correlate(events,[],gap=0)
        self.assertFalse(pair["exact_frame_sync"])
        self.assertEqual(links[0]["nearest_marker"],"UNMATCHED")
    def test_invalid_transition(self):
        with self.assertRaises(ValueError):
            correlate([event(1,"0x040A93",1,1)],[])
