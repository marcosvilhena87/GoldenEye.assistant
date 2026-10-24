"""Enemy Coordinate Discovery v1.4: stride hypothesis comparison (read-only).

Scores are descriptive, not calibrated probabilities of entity records or XYZ.
"""
import argparse
import csv
import json
from pathlib import Path
try:
    from tools.analyze_enemy_freeze_v1 import load_manifest, pairs
    from tools.analyze_enemy_freeze_v1_2 import SIZE, START, END, SHIFT
except ModuleNotFoundError as exc:
    if exc.name != "tools": raise
    from analyze_enemy_freeze_v1 import load_manifest, pairs
    from analyze_enemy_freeze_v1_2 import SIZE, START, END, SHIFT

STRIDES = (0x40, 0x48, 0x50, 0x60, 0x80)
# A noncandidate stride provides a local baseline. Each comparison has same valid window.
CONTROLS = (0x44, 0x4C, 0x54, 0x64, 0x84)
OFFSET_FIELDS = ("stride_hex","stride_bytes","is_control","compared_pairs",
                 "both_dynamic_pairs","repeated_change_pairs","repeated_rate",
                 "dynamic_rate","phase_max","phase_max_hits","phase_expected",
                 "phase_enrichment")
PHASE_FIELDS = ("stride_hex","phase","pair_count","both_dynamic","same_change",
                "dynamic_a","dynamic_b")
def signature(blobs, start=START, end=END):
    if len(blobs)!=4 or any(len(x)!=SIZE for x in blobs):
        raise ValueError("Exactly four complete snapshots required")
    if not 0<=start<end<=SIZE:raise ValueError("Invalid window")
    a,ah,b,bh=blobs
    # Atomic behavior across ON captures: dynamic iff both ON holds stable.
    return [int(a[i]==ah[i] and b[i]==bh[i] and a[i]!=b[i]) for i in range(start,end)]

def score_strides(bits,strides=STRIDES+CONTROLS):
    """Compare dynamic flags of positions separated by stride, normalized by exposure.

    Co-occurrence is a candidate statistic, not proof of shared field or record size.
    """
    n=len(bits)
    report=[];phases=[]
    for stride in strides:
        if stride<=0 or stride>=n:raise ValueError("Stride out of bounds")
        phase_groups=[dict(pair_count=0,both_dynamic=0,dynamic_a=0,dynamic_b=0) for _ in range(stride)]
        co=0;da=0;db=0
        for i in range(n-stride):
            aa=bits[i];bb=bits[i+stride]
            group=phase_groups[i%stride]
            group["pair_count"]+=1
            group["both_dynamic"]+=aa and bb
            group["dynamic_a"]+=aa
            group["dynamic_b"]+=bb
            co+=aa and bb;da+=aa;db+=bb
        comparisons=n-stride
        expected=da*db/comparisons if comparisons else 0
        rate=co/comparisons
        maxhits=max(g["both_dynamic"] for g in phase_groups)
        # Compare overlap to independence baseline; descriptively only.
        report.append(dict(stride_hex=f"0x{stride:X}",stride_bytes=stride,
            is_control=int(stride in CONTROLS),compared_pairs=comparisons,
            both_dynamic_pairs=co,repeated_change_pairs=co,
            repeated_rate=round(rate,6),dynamic_rate=round(sum(bits)/n,6),
            phase_max=maxhits,phase_max_hits=maxhits,
            phase_expected=round(expected/stride,4),
            phase_enrichment=round(co/expected,5) if expected else 0))
        phases.extend(dict(stride_hex=f"0x{stride:X}",phase=p,
            pair_count=g["pair_count"],both_dynamic=g["both_dynamic"],
            same_change=g["both_dynamic"],dynamic_a=g["dynamic_a"],
            dynamic_b=g["dynamic_b"]) for p,g in enumerate(phase_groups))
    return sorted(report,key=lambda r:(-r["phase_enrichment"],r["stride_bytes"])), phases

def inspect(session,root=Path(".")):
    root=Path(root)
    selected,err=pairs(load_manifest(root/"output/csv"/f"enemy_freeze_v1_{session}_manifest.csv"))
    if err:raise ValueError(err)
    rows=[selected[0][1]["on_stable"],selected[0][1]["on_hold"],
          selected[1][1]["on_stable"],selected[1][1]["on_hold"]]
    for row in rows:
        if row["state"]!="ON" or row["frame"]!=row["frame_after"] or row["notes"]!="raw_bus_kseg0_unvalidated":
            raise ValueError("Invalid snapshot metadata")
    blobs=[(root/r["file"]).read_bytes() for r in rows]
    a=signature(blobs)
    b=signature([v[SHIFT:]+v[:SHIFT] for v in blobs])  # remap comparison region B to A offsets
    summary_a,phase_a=score_strides(a)
    summary_b,phase_b=score_strides(b)
    for r in phase_a:r["region"]="A"
    for r in phase_b:r["region"]="B"
    merged=[]
    map_b={r["stride_hex"]:r for r in summary_b}
    for x in summary_a:
        y=map_b[x["stride_hex"]]
        merged.append({**x,"region_b_overlap":y["both_dynamic_pairs"],
            "region_b_enrichment":y["phase_enrichment"],
            "both_regions_enrichment_min":min(x["phase_enrichment"],y["phase_enrichment"])})
    merged.sort(key=lambda r:(-r["both_regions_enrichment_min"],r["stride_bytes"]))
    output=root/"output/csv"
    stem=f"enemy_freeze_v1_4_{session}"
    rank_path=output/(stem+"_stride_ranking.csv")
    phase_path=output/(stem+"_phase_profiles.csv")
    json_path=output/(stem+"_summary.json")
    if any(p.exists() for p in (rank_path,phase_path,json_path)):
        raise FileExistsError("v1.4 outputs already exist; no overwrite")
    with rank_path.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(merged[0]))
        w.writeheader();w.writerows(merged)
    with phase_path.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list((phase_a+phase_b)[0]))
        w.writeheader();w.writerows(phase_a+phase_b)
    result=dict(status="stride_candidate_only",session=session,
        epochs=[selected[0][0],selected[1][0]],mirror_shift_hex=f"0x{SHIFT:X}",
        window=[f"0x{START:X}",f"0x{END:X}"],dynamic_bytes_a=sum(a),
        dynamic_bytes_b=sum(b),stride_ranking=merged,
        caveats=["Dynamic co-occurrence is not matching values, entity identity or XYZ.",
                 "Independence enrichment assumes independent bytes and is NOT a p-value.",
                 "Window and candidate sizes chosen from prior observations; validate on independent sessions.",
                 "Full dump size checked; virtual KSEG0/RDRAM mapping unverified."])
    json_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session_id")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    result=inspect(a.session_id,a.root)
    print(json.dumps({k:v for k,v in result.items() if k!="stride_ranking"},indent=2,ensure_ascii=False))
    print("Strides:",len(result["stride_ranking"]))
if __name__=="__main__":main()
