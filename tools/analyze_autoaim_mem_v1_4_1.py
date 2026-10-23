"""v1.4.1 offline correlation of observed temporal changes (not causal inference)."""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

OFFSETS=("0x040A93","0x067D37","0x069AAD","0x0D308B","0x0D309B")
PAIR=("0x0D308B","0x0D309B")
def read_rows(path, fields, session):
    with path.open(newline="",encoding="utf-8") as stream:
        reader=csv.DictReader(stream)
        if not reader.fieldnames or set(fields)-set(reader.fieldnames):
            raise ValueError("Missing CSV columns: "+str(path))
        rows=list(reader)
    if any(row["session"]!=session for row in rows):
        raise ValueError("Mixed/wrong sessions: "+str(path))
    return rows

def correlate(events,markers,window=120,gap=3):
    if window<0 or gap<0:raise ValueError("Negative window/gap")
    ordered=sorted(events,key=lambda r:(int(r["frame"]),r["offset_hex"]))
    parsed=[]
    last={}
    for r in ordered:
        offset=r["offset_hex"]
        if offset not in OFFSETS:raise ValueError("Unknown offset")
        frame=int(r["frame"]);old=int(r["old_byte"]);new=int(r["new_byte"])
        if frame<0 or not(0<=old<=255 and 0<=new<=255) or old==new:
            raise ValueError("Invalid transition")
        if offset in last and frame<=last[offset]:
            raise ValueError("Duplicate/out-of-order transition for offset")
        last[offset]=frame
        parsed.append(dict(frame=frame,offset_hex=offset,old_byte=old,new_byte=new))
    marks=sorted([dict(frame=int(r["frame"]),label=r["label"]) for r in markers],key=lambda r:r["frame"])
    if any(m["frame"]<0 or not re.fullmatch(r"[A-Z0-9_]{1,64}",m["label"]) for m in marks):
        raise ValueError("Invalid marker")
    links=[]
    for e in parsed:
        matches=[(abs(e["frame"]-m["frame"]),m) for m in marks if abs(e["frame"]-m["frame"])<=window]
        matches.sort(key=lambda x:(x[0],x[1]["frame"]))
        if matches:
            _,m=matches[0]
            label=m["label"];delta=e["frame"]-m["frame"]
        else:label="UNMATCHED";delta=""
        links.append(dict(frame=e["frame"],offset_hex=e["offset_hex"],
                          old_byte=e["old_byte"],new_byte=e["new_byte"],
                          nearest_marker=label,delta_frames=delta,
                          temporal_status="near_marker_only" if matches else "outside_window"))
    episodes=[]
    for e in parsed:
        if not episodes or e["frame"]-episodes[-1]["end_frame"]>gap:
            episodes.append(dict(start_frame=e["frame"],end_frame=e["frame"],changes=0,offsets=set()))
        item=episodes[-1];item["end_frame"]=e["frame"];item["changes"]+=1;item["offsets"].add(e["offset_hex"])
    for e in episodes:e["offsets"]=";".join(sorted(e["offsets"]))
    a={e["frame"]:(e["old_byte"],e["new_byte"]) for e in parsed if e["offset_hex"]==PAIR[0]}
    b={e["frame"]:(e["old_byte"],e["new_byte"]) for e in parsed if e["offset_hex"]==PAIR[1]}
    union=set(a)|set(b);intersection=set(a)&set(b)
    pair=dict(offset_a=PAIR[0],offset_b=PAIR[1],changes_a=len(a),changes_b=len(b),
              shared_frames=len(intersection),different_frames=len(union-intersection),
              exact_frame_sync=(set(a)==set(b)))
    ramps=[]
    for offset in OFFSETS:
        es=[e for e in parsed if e["offset_hex"]==offset]
        run=[]
        def flush():
            if len(run)>=3:
                ramps.append(dict(offset_hex=offset,start_frame=run[0]["frame"],
                                  end_frame=run[-1]["frame"],steps=len(run),
                                  start_byte=run[0]["old_byte"],end_byte=run[-1]["new_byte"]))
        for e in es:
            if run and not(e["frame"]-run[-1]["frame"]<=gap and
                           e["old_byte"]==run[-1]["new_byte"] and e["new_byte"]>e["old_byte"]):
                flush();run=[]
            if e["new_byte"]>e["old_byte"]:run.append(e)
            else:flush();run=[]
        flush()
    return links,episodes,pair,ramps

def write_new(path,rows,columns):
    with path.open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--directory",default="output/csv")
    p.add_argument("--window",type=int,default=120)
    p.add_argument("--episode-gap",type=int,default=3)
    args=p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+",args.session):p.error("Invalid session")
    prefix=Path(args.directory)/("autoaim_mem_v1_4_"+args.session)
    events=read_rows(Path(str(prefix)+"_events.csv"),
                     ("session","frame","offset_hex","old_byte","new_byte"),args.session)
    markers=read_rows(Path(str(prefix)+"_markers.csv"),
                      ("session","frame","label"),args.session)
    links,episodes,pair,ramps=correlate(events,markers,args.window,args.episode_gap)
    outputs=[
        ("_correlation_v1_4_1.csv",links,("frame","offset_hex","old_byte","new_byte","nearest_marker","delta_frames","temporal_status")),
        ("_episodes_v1_4_1.csv",episodes,("start_frame","end_frame","changes","offsets")),
        ("_pair_sync_v1_4_1.csv",[pair],tuple(pair)),
        ("_ramps_v1_4_1.csv",ramps,("offset_hex","start_frame","end_frame","steps","start_byte","end_byte")),
    ]
    paths=[Path(str(prefix)+suffix) for suffix,_,_ in outputs]
    if any(path.exists() for path in paths):
        raise SystemExit("Output exists: refuse overwrite")
    for (suffix,rows,columns),path in zip(outputs,paths):
        write_new(path,rows,columns);print("Wrote",path)
    print("transitions",len(links),"episodes",len(episodes),"ramps",len(ramps),"pair_sync",pair["exact_frame_sync"])
    print("CAUTION: operator markers are delayed/subjective; proximity does not prove causation.")
if __name__=="__main__":main()
