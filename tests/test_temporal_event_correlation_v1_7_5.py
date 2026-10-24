import unittest
from tools.correlate_spatial_events_v1_7_5 import correlate,validate
from tools.analyze_spatial_position_v1_7_4 import OFFSETS

def fixture():
    sid="synthetic"
    frames=range(101,111)
    labels={102:("BEGIN_MOVE_LEFT","MOVE_LEFT","BEGIN"),
            108:("END_MOVE_LEFT","MOVE_LEFT","END"),
            110:("STOP","NONE","STOP")}
    markers=[dict(session=sid,frame=str(f),sample_index=str(f-100),
        label=v[0],action=v[1],phase=v[2]) for f,v in labels.items()]
    timeline=[];events=[]
    raw_a={101:"00000000",102:"11111111",103:"22222222",104:"33333333",
           105:"00000000",106:"11111111",107:"22222222",108:"33333333",
           109:"33333333",110:"33333333"}
    raw_b={f:raw_a.get(f-1,"00000000") for f in frames}
    for frame in frames:
        action="MOVE_LEFT" if 102<=frame<108 else "NONE"
        for off in OFFSETS:
            raw=raw_a[frame] if off==OFFSETS[0] else raw_b[frame] if off==OFFSETS[1] else "00000000"
            timeline.append(dict(session=sid,frame=str(frame),
                sample_index=str(frame-100),action=action,offset_hex=off,raw_hex=raw))
    mapping={(int(r["frame"]),r["offset_hex"]):r for r in timeline}
    for f in frames:
        if f==101:continue
        for off in OFFSETS:
            old=mapping[(f-1,off)]["raw_hex"];new=mapping[(f,off)]["raw_hex"]
            if old!=new:events.append(dict(session=sid,frame=str(f),action=mapping[(f,off)]["action"],
                offset_hex=off,old_hex=old,new_hex=new))
    term=[dict(session=sid,reason="stop",active_action="NONE")]
    return markers,events,timeline,term,[],sid

class TemporalCorrelationTests(unittest.TestCase):
    def test_repeated_sequence_and_lag(self):
        result=correlate(*fixture(),max_lag=2,min_sequence=3)
        summary,pairs,joint,seq,markers=result
        item=next(x for x in pairs if x["offset_a"]==OFFSETS[0] and x["offset_b"]==OFFSETS[1])
        self.assertGreaterEqual(item["nearby_matches"],4)
        self.assertTrue(any(r["offset_hex"]==OFFSETS[0] and r["occurrences"]>=2 for r in seq))
        self.assertTrue(any(r["action"]=="NONE" for r in summary))
        self.assertEqual(len(markers),3)
    def test_missing_event_rejected(self):
        x=list(fixture());x[1]=x[1][1:]
        with self.assertRaises(ValueError):correlate(*x)
    def test_corrupt_raw_rejected(self):
        x=list(fixture());x[1][0]["new_hex"]="FFFFFFFF"
        with self.assertRaises(ValueError):correlate(*x)
    def test_discontinuity_rejected(self):
        x=list(fixture());x[4]=[{"frame":"105"}]
        with self.assertRaises(ValueError):correlate(*x)
    def test_nested_marker_rejected(self):
        x=list(fixture())
        x[0].insert(1,dict(session=x[-1],frame="103",sample_index="3",
             label="BEGIN_MOVE_RIGHT",action="MOVE_RIGHT",phase="BEGIN"))
        with self.assertRaises(ValueError):correlate(*x)
if __name__=="__main__":unittest.main()
