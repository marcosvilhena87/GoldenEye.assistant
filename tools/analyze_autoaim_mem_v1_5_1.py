"""v1.5.1 Intervention Timing Audit. Offline, read-only, non-causal."""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

TRIO=("0x040A93","0x0D308B","0x0D309B")
def load(path, session, columns):
    with path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(columns)<=set(reader.fieldnames):
            raise ValueError("Invalid columns in "+str(path))
        rows=list(reader)
    if any(r["session"]!=session for r in rows):
        raise ValueError("Session mismatch in "+str(path))
    return rows

def audit(events, markers):
    changes=[]
    for r in events:
        frame=int(r["frame"]);before=int(r["old_byte"]);after=int(r["new_byte"])
        if frame<0 or before==after or not(0<=before<=255 and 0<=after<=255):
            raise ValueError("Invalid transition")
        changes.append((frame,r["offset_hex"],before,after))
    changes.sort()
    windows=[]
    current=None
    for r in sorted(markers,key=lambda x:int(x["frame"])):
        frame=int(r["frame"]);phase=r["phase"];action=r["action"]
        if phase=="BEGIN":
            if current is not None:raise ValueError("Overlapping BEGIN")
            current=(action,frame)
        elif phase=="END":
            if current is None or current[0]!=action or frame<=current[1]:
                raise ValueError("Unbalanced END")
            windows.append((action,current[1],frame));current=None
        elif phase=="STOP":
            if current is not None:raise ValueError("STOP with active window")
        else:raise ValueError("Invalid marker phase")
    if current is not None:raise ValueError("Unclosed window")
    report=[]
    for action,begin,end in windows:
        for offset in TRIO:
            rows=[c for c in changes if c[1]==offset]
            before=[c for c in rows if c[0]<begin]
            inside=[c for c in rows if begin<=c[0]<=end]
            after=[c for c in rows if c[0]>end]
            nearest_pre=before[-1] if before else None
            first_inside=inside[0] if inside else None
            first_post=after[0] if after else None
            if inside:status="within_bracket"
            elif nearest_pre:status="no_inside_change_preceded_begin"
            else:status="no_inside_change_no_preceding_transition"
            report.append(dict(action=action,offset_hex=offset,begin_frame=begin,end_frame=end,
                nearest_pre_frame=nearest_pre[0] if nearest_pre else "",
                pre_to_begin_frames=begin-nearest_pre[0] if nearest_pre else "",
                first_inside_frame=first_inside[0] if first_inside else "",
                inside_transition_count=len(inside),
                first_post_frame=first_post[0] if first_post else "",
                timing_status=status))
    # Pair timing is computed only for matching direction/value transitions.
    lead=[c for c in changes if c[1]==TRIO[0] and c[2:4] in ((0,1),(1,0))]
    pairs=[]
    for c in lead:
        for follower in TRIO[1:]:
            candidates=[x for x in changes if x[1]==follower and x[2:4]==c[2:4] and abs(x[0]-c[0])<=30]
            best=min(candidates,key=lambda x:(abs(x[0]-c[0]),x[0])) if candidates else None
            pairs.append(dict(lead_offset=TRIO[0],follower_offset=follower,
                lead_frame=c[0],from_byte=c[2],to_byte=c[3],
                follower_frame=best[0] if best else "",
                follower_minus_lead_frames=best[0]-c[0] if best else "",
                match_status="matched_by_direction_within_30_frames" if best else "no_match"))
    return report,pairs

def write(path,rows,fields):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--directory",default="output/csv")
    a=p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+",a.session):p.error("Invalid session ID")
    base=Path(a.directory)/("autoaim_mem_v1_5_"+a.session)
    changes=load(Path(str(base)+"_events.csv"),a.session,
                 ("session","frame","offset_hex","old_byte","new_byte"))
    marks=load(Path(str(base)+"_markers.csv"),a.session,
               ("session","frame","phase","action"))
    report,pairs=audit(changes,marks)
    outputs=[
        (Path(str(base)+"_timing_audit_v1_5_1.csv"),report,
         ("action","offset_hex","begin_frame","end_frame","nearest_pre_frame","pre_to_begin_frames","first_inside_frame","inside_transition_count","first_post_frame","timing_status")),
        (Path(str(base)+"_lag_audit_v1_5_1.csv"),pairs,
         ("lead_offset","follower_offset","lead_frame","from_byte","to_byte","follower_frame","follower_minus_lead_frames","match_status"))
    ]
    if any(path.exists() for path,_,_ in outputs):raise SystemExit("Refusing overwrite of existing report")
    for path,rows,fields in outputs:
        write(path,rows,fields);print("Wrote",path,"rows",len(rows))
    print("Warning: nearest preceding transition is not necessarily caused by the labelled intervention.")
if __name__=="__main__":main()
