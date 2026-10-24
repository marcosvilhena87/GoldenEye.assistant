"""v1.3: byte-level mirror and dynamic-field analysis, read-only."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

try:
    from tools.analyze_enemy_freeze_v1 import load_manifest, pairs
    from tools.analyze_enemy_freeze_v1_2 import SIZE, SHIFT, START, END
except ModuleNotFoundError as exc:
    if exc.name != "tools": raise
    from analyze_enemy_freeze_v1 import load_manifest, pairs
    from analyze_enemy_freeze_v1_2 import SIZE, SHIFT, START, END

def analyze(blobs,start=START,end=END,shift=SHIFT):
    if len(blobs)!=4 or any(len(v)!=SIZE for v in blobs):
        raise ValueError("Four full 8 MiB dumps are required")
    if not (0<=start<end and end+shift<=SIZE and shift>0):
        raise ValueError("Invalid offsets")
    a,ah,b,bh=blobs
    summary=Counter()
    fields=[]
    runs=[]
    current=None
    for o in range(start,end):
        pa=(a[o],ah[o],b[o],bh[o])
        pb=(a[o+shift],ah[o+shift],b[o+shift],bh[o+shift])
        zero_a=all(v==0 for v in pa)
        zero_b=all(v==0 for v in pb)
        stable_a=pa[0]==pa[1] and pa[2]==pa[3]
        stable_b=pb[0]==pb[1] and pb[2]==pb[3]
        change_a=pa[0]!=pa[2]
        change_b=pb[0]!=pb[2]
        identical_all=pa==pb
        common=(pa[0]==pb[0],pa[2]==pb[2])
        meaningful=stable_a and stable_b and (change_a or change_b)
        summary["bytes"]+=1
        summary["all_zero_a"]+=zero_a
        summary["all_zero_b"]+=zero_b
        summary["both_zero"]+=zero_a and zero_b
        summary["identical_all_four"]+=identical_all
        summary["same_p1"]+=common[0]
        summary["same_p2"]+=common[1]
        summary["stable_a"]+=stable_a
        summary["stable_b"]+=stable_b
        summary["stable_both"]+=stable_a and stable_b
        summary["changed_a"]+=change_a
        summary["changed_b"]+=change_b
        summary["dynamic_stable"]+=meaningful
        summary["mirror_dynamic"]+=meaningful and identical_all
        summary["independent_dynamic"]+=meaningful and not identical_all
        # Runs capture contiguous per-byte dynamics without assuming structure boundaries.
        kind=("mirrored" if identical_all else "distinct") if meaningful else "excluded"
        if current and current["kind"]==kind and current["end_exclusive"]==o:
            current["end_exclusive"]=o+1
        else:
            current=dict(start=o,end_exclusive=o+1,kind=kind)
            runs.append(current)
        if meaningful:
            fields.append(dict(offset_a=f"0x{o:06X}",offset_b=f"0x{o+shift:06X}",
                class_name=kind,stable_a=int(stable_a),stable_b=int(stable_b),
                changed_a=int(change_a),changed_b=int(change_b),
                same_p1=int(common[0]),same_p2=int(common[1]),
                raw_a=" ".join(f"{x:02X}" for x in pa),
                raw_b=" ".join(f"{x:02X}" for x in pb)))
    run_rows=[dict(start_hex=f"0x{r['start']:06X}",
                   end_exclusive_hex=f"0x{r['end_exclusive']:06X}",
                   byte_count=r["end_exclusive"]-r["start"],
                   class_name=r["kind"]) for r in runs if r["kind"]!="excluded"]
    run_rows.sort(key=lambda r:(-r["byte_count"],r["start_hex"]))
    return dict(summary),fields,run_rows

def writecsv(path,rows,fieldnames):
    with path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader();writer.writerows(rows)

def execute(session,root=Path(".")):
    root=Path(root)
    chosen,error=pairs(load_manifest(root/"output/csv"/f"enemy_freeze_v1_{session}_manifest.csv"))
    if error:raise ValueError(error)
    selected=[chosen[0][1]["on_stable"],chosen[0][1]["on_hold"],
              chosen[1][1]["on_stable"],chosen[1][1]["on_hold"]]
    for row in selected:
        if row["state"]!="ON" or row["notes"]!="raw_bus_kseg0_unvalidated" or row["frame"]!=row["frame_after"]:
            raise ValueError("Invalid capture metadata")
    blobs=[(root/row["file"]).read_bytes() for row in selected]
    counts,fields,runs=analyze(blobs)
    out=root/"output/csv"
    stem=f"enemy_freeze_v1_3_{session}"
    field_path=out/(stem+"_dynamic_fields.csv")
    runs_path=out/(stem+"_dynamic_runs.csv")
    summary_path=out/(stem+"_summary.json")
    if any(x.exists() for x in (field_path,runs_path,summary_path)):
        raise FileExistsError("Existing v1.3 output; refusing overwrite")
    writecsv(field_path,fields,["offset_a","offset_b","class_name","stable_a","stable_b",
             "changed_a","changed_b","same_p1","same_p2","raw_a","raw_b"])
    writecsv(runs_path,runs,["start_hex","end_exclusive_hex","byte_count","class_name"])
    report=dict(status="dynamic_candidate_only",session=session,
        shift_hex=f"0x{SHIFT:X}",window_start=f"0x{START:X}",window_end_exclusive=f"0x{END:X}",
        epochs=[chosen[0][0],chosen[1][0]],source_files=[r["file"] for r in selected],
        counts=counts,dynamic_runs=len(runs),
        notes=["Four captures from two ON epochs: no physical ground truth.",
               "Mirrored bytes counted once; endian interpretations not duplicated.",
               "A stable dynamic byte is not a confirmed XYZ field.",
               "Full ROM/core and KSEG0-to-RDRAM equivalence remain unvalidated."])
    summary_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session_id")
    p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    print(json.dumps(execute(args.session_id,args.root),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
