"""Compare freeze-synchronized raw memory snapshots, candidate-only.
Each file must be a same-size KSEG0 System Bus raw read; no XYZ assertions.
"""
import argparse
import csv
import json
import math
import struct
from collections import Counter
from pathlib import Path

def load_manifest(path):
    with Path(path).open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        if row["notes"]!="raw_bus_kseg0_unvalidated" or row["frame"]!=row["frame_after"]:
            raise ValueError("Unsafe dump: missing same-frame capture metadata: "+row["file"])
    return rows

def pairs(rows):
    by_epoch={}
    for row in rows:
        by_epoch.setdefault(int(row["epoch"]),{})[row["phase"]]=row
    ons=[(n,d) for n,d in sorted(by_epoch.items()) if "on_stable" in d and "on_hold" in d]
    if len(ons)<2:
        return None, "Need at least two ON epochs with both on_stable and on_hold snapshots"
    return (ons[0],ons[1]),None

def inspect(manifest,root,limit=300):
    rows=load_manifest(manifest)
    chosen,error=pairs(rows)
    if error:return {"status":"insufficient_data","reason":error}
    (a,first),(b,second)=chosen
    files=[
      first["on_stable"]["file"],first["on_hold"]["file"],
      second["on_stable"]["file"],second["on_hold"]["file"]]
    blobs=[(root/p).read_bytes() for p in files]
    lengths={len(b) for b in blobs}
    if len(lengths)!=1 or lengths!={8388608}:
        raise ValueError("Dumps must be exactly 8 MiB each, no truncation")
    candidates=[]
    n=len(blobs[0])
    for offset in range(0,n-3,4):
        s1,h1,s2,h2=(b[offset:offset+4] for b in blobs)
        if s1!=h1 or s2!=h2 or s1==s2:
            continue
        for endian,label in ((">", "big"),("<","little")):
            x,y=struct.unpack(endian+"f",s1)[0],struct.unpack(endian+"f",s2)[0]
            if not (math.isfinite(x) and math.isfinite(y) and abs(x)<1e7 and abs(y)<1e7):
                continue
            if abs(x-y)<1e-5:continue
            candidates.append({"offset_hex":f"0x{offset:06X}","encoding":"float32_"+label,
                               "p1":x,"p2":y,"delta":y-x,
                               "raw_p1":s1.hex().upper(),"raw_p2":s2.hex().upper()})
    result={"status":"candidate_only","on_epochs":[a,b],
            "snapshots":files,"candidates_total":len(candidates),
            "candidates_first":candidates[:limit],
            "caveats":["Exact byte stability requirement creates false negatives",
                       "No independent enemy instance, travel direction, or XYZ ground truth",
                       "Bus-to-RDRAM alias and loaded ROM/core still require validation",
                       "Only first two eligible ON epochs analyzed"]}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("session_id")
    ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--output")
    args=ap.parse_args()
    base=args.root/"output/csv"
    result=inspect(base/("enemy_freeze_v1_"+args.session_id+"_manifest.csv"),args.root)
    dest=Path(args.output) if args.output else base/("enemy_freeze_v1_"+args.session_id+"_candidates.json")
    if dest.exists():raise FileExistsError(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="candidates_first"},indent=2,ensure_ascii=False))
    print("Report:",dest)
if __name__=="__main__":main()
