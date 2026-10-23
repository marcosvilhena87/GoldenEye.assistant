"""Read-only v1.5 semantic-window comparison. Does not infer field meaning."""
import argparse,csv,re
from pathlib import Path
OFFSETS=("0x040A93","0x067D37","0x069AAD","0x0D308B","0x0D309B")
def load(path,sid,columns):
    with path.open(newline="",encoding="utf-8") as f:
        d=csv.DictReader(f)
        if not d.fieldnames or not set(columns).issubset(d.fieldnames):raise ValueError("Bad header: "+str(path))
        rows=list(d)
    if any(r["session"]!=sid for r in rows):raise ValueError("Session mismatch")
    return rows
def analyze(samples,marks):
    by={}
    for row in samples:
        k=(int(row["frame"]),row["offset_hex"])
        if k in by or k[1] not in OFFSETS:raise ValueError("Duplicate/unknown sample")
        v=int(row["byte"])
        if not 0<=v<=255:raise ValueError("Invalid byte")
        by[k]=v
    frames=sorted({f for f,o in by})
    if not frames or any((f,o) not in by for f in frames for o in OFFSETS):
        raise ValueError("Incomplete frame")
    ordered=sorted(marks,key=lambda r:int(r["frame"]))
    if ordered!=marks:raise ValueError("Out-of-order markers")
    active=None;windows=[]
    for row in marks:
        frame=int(row["frame"]);phase=row["phase"];action=row["action"]
        if phase=="BEGIN" and active is None:active=(action,frame)
        elif phase=="END" and active and active[0]==action:
            if frame<=active[1]:raise ValueError("Empty action window")
            windows.append((action,active[1],frame));active=None
        elif phase=="STOP" and active is None:pass
        else:raise ValueError("Unbalanced markers")
    if active:raise ValueError("Unclosed action")
    out=[]
    for action,start,end in windows:
        prior=[f for f in frames if f<start]
        inside=[f for f in frames if start<=f<=end]
        following=[f for f in frames if f>end]
        for off in OFFSETS:
            values=[by[(f,off)] for f in inside]
            if not values:raise ValueError("Missing window samples")
            before=by[(prior[-1],off)] if prior else ""
            after=by[(following[0],off)] if following else ""
            changes=sum(a!=b for a,b in zip(values,values[1:]))
            out.append(dict(action=action,begin_frame=start,end_frame=end,offset_hex=off,
                before_byte=before,begin_byte=values[0],end_byte=values[-1],after_byte=after,
                distinct_values=len(set(values)),inside_changes=changes,
                observed_change=("yes" if changes or (before!="" and before!=values[0]) else "no"),
                conclusion="descriptive_only"))
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--directory",default="output/csv");args=p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+",args.session):p.error("Bad ID")
    prefix=Path(args.directory)/f"autoaim_mem_v1_5_{args.session}"
    samples=load(Path(str(prefix)+"_timeline.csv"),args.session,("session","frame","offset_hex","byte"))
    markers=load(Path(str(prefix)+"_markers.csv"),args.session,("session","frame","action","phase"))
    rows=analyze(samples,markers)
    if not rows:raise SystemExit("No complete action windows")
    output=Path(str(prefix)+"_semantic_windows.csv")
    with output.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print("Wrote",output,"windows",len(rows)//5,"records",len(rows))
    print("Descriptive evidence only; no validated symbol or horizontal correction identified.")
if __name__=="__main__":main()
