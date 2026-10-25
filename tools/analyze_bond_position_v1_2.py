"""Bond v1.2: bounded marker-relative analysis, never auto-validates axes."""
import csv,json,math,pathlib,statistics,sys,collections
OFFSETS={"0x0D33E8","0x0D33EC","0x0D33F0","0x0D33F4"}
PAIR={"BEGIN_FORWARD":"END_FORWARD","BEGIN_BACK":"END_BACK","BEGIN_LEFT":"END_LEFT","BEGIN_RIGHT":"END_RIGHT","BEGIN_ROTATE":"END_ROTATE"}
def analyze(sid,root=pathlib.Path("output/csv")):
    stem=root/("bond_position_v1_2_"+sid)
    def read(suffix):
        with pathlib.Path(str(stem)+suffix).open(newline="",encoding="utf-8") as f:
            return list(csv.DictReader(f))
    timeline=read("_timeline.csv");marks=read("_markers.csv");ends=read("_termination.csv");disc=read("_discontinuities.csv")
    if not timeline or len(timeline)%4: raise ValueError("Invalid/incomplete timeline")
    byoff=collections.defaultdict(list);aliasbad=nonfinite=0
    for row in timeline:
        if row["session"]!=sid or row["offset_hex"] not in OFFSETS: raise ValueError("Unexpected timeline record")
        aliasbad+=row["alias_equal"]!="1"
        nonfinite+=row["finite"]!="1"
        if row["finite"]=="1":
            v=float(row["float32_be"])
            if math.isfinite(v): byoff[row["offset_hex"]].append((int(row["frame"]),v))
    frames=sorted({int(r["frame"]) for r in timeline})
    if len(frames)*4!=len(timeline): raise ValueError("Missing/duplicate frame-offset records")
    events=[];pending={}
    for row in marks:
        label=row["label"];frame=int(row["frame"])
        if label in PAIR: pending[label]=(frame,label)
        if label in PAIR.values():
            start=next((k for k,v in PAIR.items() if v==label),None)
            if start in pending:
                first,_=pending.pop(start)
                if frame>first: events.append((start,first,frame))
    def get_at(points,frame):
        left=[(f,v) for f,v in points if f<=frame]
        return left[-1][1] if left else None
    intervals=[]
    for label,start,finish in events:
        sample={"phase":label,"begin_frame":start,"end_frame":finish,"offsets":{}}
        for addr,pairs in sorted(byoff.items()):
            inside=[v for f,v in pairs if start<=f<finish]
            if inside:
                sample["offsets"][addr]={"delta":inside[-1]-inside[0],"range":max(inside)-min(inside),"samples":len(inside)}
        intervals.append(sample)
    writes=[]
    pre=[int(m["frame"]) for m in marks if m["label"]=="WRITE_PRE"]
    applied=[int(m["frame"]) for m in marks if m["label"]=="WRITE_APPLIED"]
    for a in applied:
        p=max((f for f in pre if f<a),default=None)
        record={"applied_marker_frame":a,"pre_marker_frame":p,"status":"unverified_manual_intervention","offsets":{}}
        for addr,points in byoff.items():
            before=get_at(points,a-1)
            if before is None: continue
            checkpoints={}
            for step in (0,1,30,120):
                later=get_at(points,a+step)
                checkpoints[str(step)]=None if later is None else later-before
            record["offsets"][addr]=checkpoints
        writes.append(record)
    result={"session":sid,"timeline_rows":len(timeline),"frames":len(frames),"alias_mismatches":aliasbad,"nonfinite":nonfinite,"termination":ends,"discontinuities":disc,"intervals":intervals,"write_marker_checks":writes,"flags":{"clean_stop":bool(ends) and ends[-1]["reason"]=="stop","axis_validated":False,"write_persistence_validated":False},"limitations":["Marker timestamps do not verify physical user actions","No independent camera/geometry truth","Write checkpoints are observational, not proof of actual write","Missing unmarked movements or mid-interval drift can invalidate semantics"]}
    target=pathlib.Path(str(stem)+"_analysis.json")
    if target.exists(): raise FileExistsError(target)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result,target
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: python -m tools.analyze_bond_position_v1_2 SID")
    result,out=analyze(sys.argv[1])
    print("Audit",out,"frames",result["frames"],"alias mismatches",result["alias_mismatches"],"intervals",len(result["intervals"]),"clean_stop",result["flags"]["clean_stop"])
