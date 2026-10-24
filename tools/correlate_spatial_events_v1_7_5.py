"""Temporal Event Correlation v1.7.5: offline, read-only v1.7.4 CSV audit.

Find exact RAW transitions shared at the same/nearby frames, repeated joint
states, and signed frame distances to actual BEGIN/END markers. These are
descriptive associations, NOT causal or spatial confirmations.
"""
import argparse
import csv
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

try:
    from tools.analyze_spatial_position_v1_7_4 import OFFSETS, ACTIONS
except ModuleNotFoundError:
    from analyze_spatial_position_v1_7_4 import OFFSETS, ACTIONS

EVENT_FIELDS=("session","frame","action","offset_hex","old_hex","new_hex",
              "inside_labeled_phase","nearest_marker_label","nearest_marker_frame",
              "signed_frames_from_marker","absolute_frames_from_marker","status")
PAIR_FIELDS=("session","offset_a","offset_b","total_events_a","total_events_b",
             "simultaneous_frames","nearby_matches","median_signed_lag_b_minus_a",
             "max_lag","status")
STATE_FIELDS=("session","offsets","raw_state_tuple","episodes","start_frames",
              "status")
SEQUENCE_FIELDS=("session","offset_hex","sequence_length","transition_signature",
                 "occurrences","start_frames","status")
MARKER_FIELDS=("session","frame","label","action","phase","status")

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as handle:
        return list(csv.DictReader(handle))

def require_int(value,name):
    try: result=int(value)
    except (TypeError,ValueError):raise ValueError(f"Invalid {name}") from None
    if result<0:raise ValueError(f"Negative {name}")
    return result

def validate(markers,events,timeline,term,discontinuities,sid):
    if discontinuities:raise ValueError("timeline discontinuity")
    if len(term)!=1 or term[0].get("session")!=sid or term[0].get("reason") not in ("stop","frame_limit") or term[0].get("active_action")!="NONE":
        raise ValueError("invalid or incomplete termination")
    if not markers or not timeline:raise ValueError("missing marker/timeline evidence")
    times=[];prior_sample=0;open_phase=None
    for marker in markers:
        if marker.get("session")!=sid:raise ValueError("marker session mismatch")
        frame=require_int(marker["frame"],"marker frame")
        sample=require_int(marker["sample_index"],"marker sample_index")
        if sample<=prior_sample:raise ValueError("unsorted markers")
        prior_sample=sample
        label=marker.get("label")
        if label=="STOP":
            if open_phase or marker.get("phase")!="STOP":raise ValueError("invalid STOP")
        else:
            phase,_,action=label.partition("_")
            if phase not in ("BEGIN","END") or action not in ACTIONS or marker.get("action")!=action or marker.get("phase")!=phase:
                raise ValueError("invalid bracket")
            if phase=="BEGIN":
                if open_phase is not None:raise ValueError("nested phase")
                open_phase=action
            else:
                if open_phase!=action:raise ValueError("unmatched end")
                open_phase=None
        times.append((frame,label,sample))
    if open_phase:raise ValueError("unfinished phase")
    by_frame=defaultdict(dict)
    min_frame=None;last=None
    for row in timeline:
        if row.get("session")!=sid or row.get("offset_hex") not in OFFSETS:
            raise ValueError("invalid timeline row")
        frame=require_int(row["frame"],"timeline frame")
        idx=require_int(row["sample_index"],"sample index")
        raw=row.get("raw_hex","").upper()
        if not re.fullmatch(r"[0-9A-F]{8}",raw):raise ValueError("invalid raw")
        if row["offset_hex"] in by_frame[frame]:raise ValueError("duplicate sample")
        by_frame[frame][row["offset_hex"]]=(idx,raw,row.get("action"))
    frames=sorted(by_frame)
    if not frames:raise ValueError("empty timeline")
    for j,frame in enumerate(frames):
        if j and frame!=frames[j-1]+1:raise ValueError("frame gap")
        if len(by_frame[frame])!=len(OFFSETS):raise ValueError("missing offset sample")
        for idx,raw,action in by_frame[frame].values():
            if idx!=j+1:raise ValueError("sample gap")
    for frame,label,sample in times:
        if frame not in by_frame or next(iter(by_frame[frame].values()))[0]!=sample:
            raise ValueError("marker/timeline disagreement")
    current=None;marker_by_frame={f:label for f,label,_ in times}
    for frame in frames:
        label=marker_by_frame.get(frame)
        if label:
            if label=="STOP":current=None
            else:
                phase,_,action=label.partition("_")
                current=action if phase=="BEGIN" else None
        for idx,raw,action in by_frame[frame].values():
            if action!=(current or "NONE"):
                raise ValueError("timeline action inconsistent with marker")
    observed={}
    for row in events:
        if row.get("session")!=sid or row.get("offset_hex") not in OFFSETS:raise ValueError("invalid event row")
        frame=require_int(row["frame"],"event frame")
        offset=row["offset_hex"];key=(frame,offset)
        if key in observed:raise ValueError("duplicate event")
        if frame not in by_frame or frame==frames[0]:raise ValueError("out-of-range event")
        previous=by_frame[frame-1][offset][1]
        new=by_frame[frame][offset][1]
        if previous==new or row.get("old_hex","").upper()!=previous or row.get("new_hex","").upper()!=new:
            raise ValueError("event RAW mismatch")
        if row.get("action")!=by_frame[frame][offset][2]:raise ValueError("event action mismatch")
        observed[key]=row
    expected={(frame,off) for frame in frames[1:] for off in OFFSETS if by_frame[frame-1][off][1]!=by_frame[frame][off][1]}
    if set(observed)!=expected:raise ValueError("missing or spurious events")
    return frames,by_frame,sorted(times),sorted(events,key=lambda r:(int(r["frame"]),r["offset_hex"]))

def median(xs):
    if not xs:return None
    ordered=sorted(xs);n=len(xs)
    return ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2

def correlate(markers,events,timeline,term,discontinuities,sid,max_lag=4,min_sequence=3):
    if max_lag<0 or min_sequence<2:raise ValueError("invalid thresholds")
    frames,data,markers,events=validate(markers,events,timeline,term,discontinuities,sid)
    summary=[]
    for event in events:
        frame=int(event["frame"])
        mframe,label,_=min(markers,key=lambda m:(abs(frame-m[0]),m[0],m[1]))
        summary.append(dict(session=sid,frame=frame,action=event["action"],
            offset_hex=event["offset_hex"],old_hex=event["old_hex"],
            new_hex=event["new_hex"],inside_labeled_phase=event["action"]!="NONE",
            nearest_marker_label=label,nearest_marker_frame=mframe,
            signed_frames_from_marker=frame-mframe,
            absolute_frames_from_marker=abs(frame-mframe),
            status="temporal_association_not_causality"))
    event_frames=defaultdict(list)
    for event in events:event_frames[event["offset_hex"]].append(int(event["frame"]))
    pairs=[]
    for a,b in combinations(OFFSETS,2):
        aa=event_frames[a];bb=event_frames[b]
        coincident=len(set(aa)&set(bb))
        # Strict one-to-one greedy nearest pairing within max_lag:
        candidates=sorted((abs(y-x),x,y) for x in aa for y in bb if abs(y-x)<=max_lag)
        used_a=set();used_b=set();lags=[]
        for distance,x,y in candidates:
            if x not in used_a and y not in used_b:
                used_a.add(x);used_b.add(y);lags.append(y-x)
        pairs.append(dict(session=sid,offset_a=a,offset_b=b,total_events_a=len(aa),
            total_events_b=len(bb),simultaneous_frames=coincident,
            nearby_matches=len(lags),median_signed_lag_b_minus_a=median(lags),
            max_lag=max_lag,status="candidate_synchrony_not_shared_meaning"))
    # Recurrent exact RAW joint-state signatures over all eight offsets, compressed
    # into contiguous episodes, not treating every repeated frame as a new episode.
    states=defaultdict(list);previous_state=None
    for frame in frames:
        state=tuple(data[frame][off][1] for off in OFFSETS)
        if state!=previous_state:states[state].append(frame)
        previous_state=state
    joint=[]
    for state,starts in sorted(states.items(),key=lambda it:(-len(it[1]),it[1][0])):
        if len(starts)<2:continue
        joint.append(dict(session=sid,offsets=";".join(OFFSETS),
            raw_state_tuple=";".join(state),episodes=len(starts),
            start_frames=";".join(map(str,starts)),
            status="repeated_joint_state_not_game_semantics"))
    # Exact repeated transition runs per offset. A run of length N means N
    # consecutive *events* (not necessarily consecutive frames).
    sequences=[]
    by_offset=defaultdict(list)
    for event in events:by_offset[event["offset_hex"]].append(event)
    for off,rows in by_offset.items():
        if len(rows)<min_sequence:continue
        patterns=defaultdict(list)
        for i in range(len(rows)-min_sequence+1):
            sub=rows[i:i+min_sequence]
            signature=tuple((r["old_hex"],r["new_hex"]) for r in sub)
            patterns[signature].append(int(sub[0]["frame"]))
        for signature,starts in patterns.items():
            if len(starts)<2:continue
            sequences.append(dict(session=sid,offset_hex=off,
                sequence_length=min_sequence,
                transition_signature=";".join(x+">"+y for x,y in signature),
                occurrences=len(starts),start_frames=";".join(map(str,starts)),
                status="repeated_raw_sequence_not_causal"))
    sequences.sort(key=lambda x:(-x["occurrences"],x["offset_hex"],int(x["start_frames"].split(";")[0])))
    annotated=[dict(session=sid,frame=frame,label=label,action="NONE" if label=="STOP" else label.partition("_")[2],
              phase="STOP" if label=="STOP" else label.partition("_")[0],
              status="operator_marker_not_measured_input") for frame,label,_ in markers]
    return summary,pairs,joint,sequences,annotated

def write_exclusive(path,fields,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)

def run(root,sid,max_lag=4,min_sequence=3):
    if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid session")
    prefix=root/"output"/"csv"/f"spatial_v1_7_4_{sid}"
    src=lambda suffix:read_csv(Path(str(prefix)+suffix))
    result=correlate(src("_markers.csv"),src("_events.csv"),
                     src("_timeline.csv"),src("_termination.csv"),
                     src("_discontinuities.csv"),sid,max_lag,min_sequence)
    dest=root/"output"/"csv"/f"spatial_v1_7_5_{sid}"
    files=[(Path(str(dest)+"_event_marker_distances.csv"),EVENT_FIELDS,result[0]),
           (Path(str(dest)+"_paired_offsets.csv"),PAIR_FIELDS,result[1]),
           (Path(str(dest)+"_repeated_joint_states.csv"),STATE_FIELDS,result[2]),
           (Path(str(dest)+"_repeated_sequences.csv"),SEQUENCE_FIELDS,result[3]),
           (Path(str(dest)+"_markers.csv"),MARKER_FIELDS,result[4])]
    if any(path.exists() for path,_,_ in files):raise FileExistsError("v1.7.5 outputs exist; refusing overwrite")
    for path,fields,rows in files:write_exclusive(path,fields,rows)
    return files

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--max-lag",type=int,default=4)
    p.add_argument("--sequence-length",type=int,default=3)
    args=p.parse_args()
    files=run(args.root.resolve(),args.session,args.max_lag,args.sequence_length)
    for path,_,rows in files:print(f"Wrote {path} rows={len(rows)}")
    print("Correlations describe RAW data and operator labels; no Bond positions validated.")
if __name__=="__main__":main()
