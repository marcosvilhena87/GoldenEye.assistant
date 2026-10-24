"""v1.7 Graphics Buffer Exclusion & Coordinate Search Refinement.

Read-only analysis of existing v1.6 captures. Evidence-labelled, no XYZ claims.
"""
import argparse
import csv
import json
import math
import struct
from collections import Counter
from pathlib import Path
try:
    from tools.analyze_enemy_freeze_v1_6 import REGIONS,validate_manifest
except ModuleNotFoundError as exc:
    if exc.name!="tools":raise
    from analyze_enemy_freeze_v1_6 import REGIONS,validate_manifest

# Common 8-byte display-list first-word opcodes, *microcode-dependent*.
DL_OPS={0xB6,0xB7,0xB9,0xBA,0xBC,0xDE,0xDF,0xE7,0xF8,0xFB,0xFC,0xFD,0x06}
STRONG={0xE7,0xF8,0xFB,0xFC}
WINDOW=64
MIN_HITS=3
def scan_graphics(data):
    """Score fully aligned 8-byte words over sliding 64-byte windows.
    A single opcode can never trigger a suspicious window.
    """
    suspicious=set();windows=[]
    for start in range(0,len(data)-WINDOW+1,8):
        ops=[data[pos] for pos in range(start,start+WINDOW,8)]
        hits=sum(op in DL_OPS for op in ops)
        strong=sum(op in STRONG for op in ops)
        unique=len(set(op for op in ops if op in DL_OPS))
        flagged=hits>=MIN_HITS and unique>=2 and strong>=1
        if flagged:suspicious.update(range(start,start+WINDOW))
        windows.append(dict(relative_start=start,hit_count=hits,strong_hits=strong,
                            unique_opcodes=unique,suspected=int(flagged)))
    return suspicious,windows

def decode_float(raw,endian):
    value=struct.unpack(endian+"f",raw)[0]
    return value if math.isfinite(value) and abs(value)<1000000 else None

def scan_numeric(keys,epochs,graphics_masks):
    results=[];counts=Counter()
    cam=all((epochs[-1],"camera",r) in keys for r in REGIONS)
    for region,(base,size) in REGIONS.items():
        seq=[keys[(e,"stable",region)] for e in epochs]
        hold=[keys[(e,"hold",region)] for e in epochs]
        control=keys.get((epochs[-1],"camera",region))
        mask=graphics_masks[region]
        for off in range(0,size-3,4):
            vals=[v[off:off+4] for v in seq]
            if any(seq[j][off:off+4]!=hold[j][off:off+4] for j in range(3)):continue
            if vals[0]==vals[1] or vals[1]==vals[2]:continue
            counts["stable_dynamic_words"]+=1
            camera_changed=control is not None and control[off:off+4]!=vals[2]
            graphics=any(k in mask for k in range(off,off+4))
            for fmt,endian in (("float32_be",">"),("float32_le","<")):
                numbers=[decode_float(x,endian) for x in vals]
                if any(v is None for v in numbers):continue
                delta1=numbers[1]-numbers[0];delta2=numbers[2]-numbers[1]
                if not all(math.isfinite(x) for x in (delta1,delta2)):continue
                if not(0.0001<=abs(delta1)<=100000 and 0.0001<=abs(delta2)<=100000):continue
                # Heuristic only; no ground truth for physical speed or direction.
                plausible=not camera_changed and not graphics
                results.append(dict(region=region,offset_hex=f"0x{base+off:06X}",
                   format=fmt,p1=round(numbers[0],6),p2=round(numbers[1],6),
                   p3=round(numbers[2],6),delta12=round(delta1,6),
                   delta23=round(delta2,6),camera_available=int(cam),
                   camera_changed=int(camera_changed),graphics_context=int(graphics),
                   status="numeric_candidate_only" if plausible else "review_graphics_or_camera"))
                counts["numeric_interpretations"]+=1
    results.sort(key=lambda x:(x["graphics_context"],x["camera_changed"],x["region"],x["offset_hex"],x["format"]))
    return results,dict(counts)

def analyze(keys,epochs):
    masks={};windows=[];counts=Counter()
    for region in REGIONS:
        masks[region]=set()
        for epoch in epochs:
            raw=keys[(epoch,"stable",region)]
            marked,rows=scan_graphics(raw)
            masks[region].update(marked)
            windows.extend(dict(region=region,epoch=epoch,**row) for row in rows if row["suspected"])
        counts[f"region{region}_graphic_context_bytes"]=len(masks[region])
        counts[f"region{region}_graphic_windows"]=sum(x["region"]==region for x in windows)
    numeric,ncounts=scan_numeric(keys,epochs,masks)
    counts.update(ncounts)
    counts["numeric_without_graphics_or_camera"]=sum(r["status"]=="numeric_candidate_only" for r in numeric)
    return windows,numeric,dict(counts)

def writecsv(path,rows,fields):
    with path.open("x",encoding="utf8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def execute(session,root=Path(".")):
    root=Path(root)
    with (root/"output/csv"/f"enemy_freeze_v1_6_{session}_manifest.csv").open(encoding="utf8",newline="") as f:
        keys,epochs=validate_manifest(list(csv.DictReader(f)),root)
    windows,numeric,counts=analyze(keys,epochs)
    base=root/"output/csv"/f"enemy_freeze_v1_7_{session}"
    files=[Path(str(base)+"_"+name) for name in ("graphics_windows.csv","numeric_candidates.csv","summary.json")]
    if any(p.exists() for p in files):raise FileExistsError("v1.7 report exists; preserving results")
    writecsv(files[0],windows,["region","epoch","relative_start","hit_count","strong_hits","unique_opcodes","suspected"])
    writecsv(files[1],numeric,["region","offset_hex","format","p1","p2","p3","delta12","delta23",
            "camera_available","camera_changed","graphics_context","status"])
    report=dict(status="exploratory_graphics_exclusion_only",session=session,epochs=epochs,
        counts=counts,heuristic=dict(window_bytes=WINDOW,minimum_opcodes=MIN_HITS),
        notes=["Common F3DEX/RDP opcode byte patterns are microcode-dependent, not proven display lists.",
               "Graphical context labels are soft exclusions; false positives/negatives expected.",
               "Only three already-captured windows available; no search of remaining RAM.",
               "Float32 endian values are candidate interpretations, not verified positions.",
               "No enemy identity, physical motion direction/distance, ROM/core verification."])
    files[2].write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("session_id");p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args();print(json.dumps(execute(a.session_id,a.root),indent=2,ensure_ascii=False))
