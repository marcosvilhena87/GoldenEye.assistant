import unittest
from tools.analyze_autoaim_mem_v1_5_1 import audit
class TimingAuditTests(unittest.TestCase):
    def test_pre_marker_and_two_frame_lag(self):
        events=[]
        for frame,off in [(197159,"0x040A93"),(197161,"0x0D308B"),(197161,"0x0D309B"),
                          (203527,"0x040A93"),(203529,"0x0D308B"),(203529,"0x0D309B")]:
            old,new=(1,0) if frame<200000 else (0,1)
            events.append(dict(frame=str(frame),offset_hex=off,old_byte=str(old),new_byte=str(new)))
        marks=[dict(frame="197539",phase="BEGIN",action="AUTOAIM_OFF"),
               dict(frame="200230",phase="END",action="AUTOAIM_OFF"),
               dict(frame="204224",phase="BEGIN",action="AUTOAIM_ON"),
               dict(frame="204896",phase="END",action="AUTOAIM_ON"),
               dict(frame="206522",phase="STOP",action="NONE")]
        result,pairs=audit(events,marks)
        self.assertEqual(len(result),6)
        self.assertEqual(result[0]["pre_to_begin_frames"],380)
        self.assertEqual(result[3]["pre_to_begin_frames"],697)
        self.assertEqual([p["follower_minus_lead_frames"] for p in pairs],[2,2,2,2])
        self.assertTrue(all(x["inside_transition_count"]==0 for x in result))
    def test_inside_window(self):
        events=[dict(frame="12",offset_hex="0x040A93",old_byte="1",new_byte="0")]
        marks=[dict(frame="10",phase="BEGIN",action="AUTOAIM_OFF"),
               dict(frame="20",phase="END",action="AUTOAIM_OFF")]
        r,_=audit(events,marks)
        self.assertEqual(r[0]["timing_status"],"within_bracket")
    def test_unbalanced(self):
        with self.assertRaises(ValueError):
            audit([],[dict(frame="2",phase="END",action="AUTOAIM_OFF")])
