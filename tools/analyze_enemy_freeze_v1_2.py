"""Enemy Coordinate Discovery v1.2: raw repeated-structure validation.
Reads existing four 8 MiB dumps, never writes emulator memory or source dumps.
"""
import argparse
import csv
import json
from pathlib import Path

try:
    from tools.analyze_enemy_freeze_v1 import load_manifest, pairs
except ModuleNotFoundError as exc:
    if exc.name != "tools":
        raise
    from analyze_enemy_freeze_v1 import load_manifest, pairs

SIZE = 8388608
SHIFT = 0x11800
START = 0x0D5000
END = 0x0D8500
BLOCK = 256
CONTROLS = (0x10000, 0x10800, 0x11000, 0x11800, 0x12000, 0x12800, 0x13000)

def comparison(a, b, start, end, shift):
    """Same-index byte comparisons over a fixed original-A window."""
    if shift < 0 or start < 0 or end > len(a) or end + shift > len(a):
        raise ValueError("Invalid window/shift")
    left = a[start:end]
    right = b[start + shift:end + shift]
    same = sum(x == y for x, y in zip(left, right))
    return same, len(left)

def classify(a, b, shift, start=START, end=END, block=BLOCK):
    if len(a) != len(b) or not (0 <= start < end <= len(a) - shift):
        raise ValueError("Invalid compare configuration")
    result=[]
    for lo in range(start,end,block):
        hi=min(end,lo+block)
        same,total=comparison(a,b,lo,hi,shift)
        result.append(dict(start_hex=f"0x{lo:06X}",end_exclusive_hex=f"0x{hi:06X}",
                           shifted_start_hex=f"0x{lo+shift:06X}",
                           same_bytes=same,total_bytes=total,
                           equality_ratio=round(same/total,6)))
    return result

def dynamics(p1a,p1h,p2a,p2h,start=START,end=END,shift=SHIFT):
    """Compute paired-region identity across two frozen epochs, raw bytes, no float filter."""
    if any(len(x)!=SIZE for x in (p1a,p1h,p2a,p2h)):
        raise ValueError("Requires four full 8 MiB snapshots")
    if start<0 or end+shift>SIZE or end<=start:
        raise ValueError("Invalid region")
    stats={}
    rows=[]
    for label,blob in (("p1",p1a),("p1_hold",p1h),("p2",p2a),("p2_hold",p2h)):
        count,total=comparison(blob,blob,start,end,shift)
        stats[label]=dict(equal=count,total=total,ratio=round(count/total,6))
    flags={}
    for i in range(start,end):
        equal1=p1a[i]==p1a[i+shift]
        equal2=p2a[i]==p2a[i+shift]
        tag=("equal" if equal1 else "different")+"_"+("equal" if equal2 else "different")
        flags[tag]=flags.get(tag,0)+1
        stable_a=p1a[i]==p1h[i] and p2a[i]==p2h[i]
        stable_b=p1a[i+shift]==p1h[i+shift] and p2a[i+shift]==p2h[i+shift]
        changed_a=p1a[i]!=p2a[i];changed_b=p1a[i+shift]!=p2a[i+shift]
        if equal1!=equal2 or (changed_a != changed_b):
            rows.append(dict(offset_a=f"0x{i:06X}",offset_b=f"0x{i+shift:06X}",
                p1_equal=int(equal1),p2_equal=int(equal2),
                stable_a=int(stable_a),stable_b=int(stable_b),
                changed_a=int(changed_a),changed_b=int(changed_b),
                p1_a=f"{p1a[i]:02X}",p1_b=f"{p1a[i+shift]:02X}",
                p2_a=f"{p2a[i]:02X}",p2_b=f"{p2a[i+shift]:02X}"))
    return stats,flags,rows

def process(blobs,start=START,end=END,shift=SHIFT,controls=CONTROLS):
    if len(blobs)!=4 or any(len(b)!=SIZE for b in blobs):
        raise ValueError("Four 8 MiB snapshots required")
    p1,p1h,p2,p2h=blobs
    stats,classes,changed=dynamics(*blobs,start=start,end=end,shift=shift)
    control=[]
    for delta in controls:
        if end+delta>SIZE:raise ValueError("Control shift outside dump")
        a,n=comparison(p1,p1,start,end,delta)
        b,_=comparison(p2,p2,start,end,delta)
        control.append(dict(shift_hex=f"0x{delta:X}",p1_equal=a,p2_equal=b,
                            total=n,p1_ratio=round(a/n,6),p2_ratio=round(b/n,6),
                            is_target=int(delta==shift)))
    windows=classify(p1,p1,shift,start,end)
    return stats,classes,changed,control,windows

def output_csv(path,rows,fields):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def execute(session,root=Path("."),start=START,end=END,shift=SHIFT):
    root=Path(root)
    manifest=root/"output/csv"/f"enemy_freeze_v1_{session}_manifest.csv"
    selected,error=pairs(load_manifest(manifest))
    if error:raise ValueError(error)
    rows=[selected[0][1]["on_stable"],selected[0][1]["on_hold"],
          selected[1][1]["on_stable"],selected[1][1]["on_hold"]]
    for row in rows:
        if row["frame"] != row["frame_after"] or row["notes"]!="raw_bus_kseg0_unvalidated":
            raise ValueError("Non-atomic or invalid snapshot metadata")
        if row["state"]!="ON":raise ValueError("Expected ON snapshot")
    blobs=[(root/r["file"]).read_bytes() for r in rows]
    stats,classes,changed,control,windows=process(blobs,start,end,shift)
    output=root/"output/csv"
    prefix=f"enemy_freeze_v1_2_{session}"
    paths={k:output/(prefix+"_"+k+".csv") for k in
          ("shift_controls","window_equality","byte_divergences")}
    summary=output/(prefix+"_summary.json")
    if any(p.exists() for p in [*paths.values(),summary]):
        raise FileExistsError("Report exists; original analysis preserved")
    output_csv(paths["shift_controls"],control,
               ["shift_hex","p1_equal","p2_equal","total","p1_ratio","p2_ratio","is_target"])
    output_csv(paths["window_equality"],windows,
               ["start_hex","end_exclusive_hex","shifted_start_hex","same_bytes","total_bytes","equality_ratio"])
    output_csv(paths["byte_divergences"],changed,
               ["offset_a","offset_b","p1_equal","p2_equal","stable_a","stable_b","changed_a","changed_b","p1_a","p1_b","p2_a","p2_b"])
    info=dict(status="structural_candidate_only",session=session,shift_hex=f"0x{shift:X}",
        window=[f"0x{start:X}",f"0x{end:X}"],epochs=[selected[0][0],selected[1][0]],
        source_files=[r["file"] for r in rows],equality=stats,classes=classes,
        divergence_rows=len(changed),comparisons=control,
        caveats=["Within-session raw byte equality only; does not identify enemy coordinates.",
                 "Control shifts are nearby shifts, not a null-distribution or significance test.",
                 "The same bytes are interpreted once independent of float endian alternatives.",
                 "Fixed exploratory window; full 8 MiB each input checked.",
                 "KSEG0/RDRAM alias, ROM and core remain unverified."])
    summary.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return info

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session_id")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(execute(a.session_id,a.root),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
