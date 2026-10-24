"""v1.8 full 8MiB float candidate screen; graphics context is a label, never excluded."""
import argparse,csv,json,math,struct
from collections import Counter
from pathlib import Path
SIZE=0x800000
OPCODES={0xB6,0xB7,0xB9,0xBA,0xBC,0xDE,0xDF,0xE7,0xF8,0xFB,0xFC,0xFD,0x06}
STRONG={0xE7,0xF8,0xFB,0xFC}
def read_capture(session,root):
    file=root/"output/csv"/f"enemy_freeze_v1_8_{session}_manifest.csv"
    with file.open(newline="",encoding="utf8") as f:rows=list(csv.DictReader(f))
    blobs={};seen=set()
    for row in rows:
        epoch=int(row["epoch"]);phase=row["phase"]
        if phase not in ("stable","hold","camera") or epoch not in (1,2,3):
            raise ValueError("Unexpected epoch/phase")
        key=(epoch,phase)
        if key in seen:raise ValueError("Duplicate capture")
        seen.add(key)
        if row["session"]!=session or row["state"]!="ON" or row["frame"]!=row["after_frame"] or row["notes"]!="same_frame_kseg0_unvalidated" or row["start_hex"]!="0x000000" or int(row["bytes"])!=SIZE:
            raise ValueError("Invalid capture metadata")
        blob=(root/row["file"]).read_bytes()
        if len(blob)!=SIZE:raise ValueError("Incomplete full RAM dump")
        blobs[key]=blob
    for epoch in (1,2,3):
        for phase in ("stable","hold"):
            if (epoch,phase) not in blobs:raise ValueError("Missing epoch/phase")
    return blobs

def numeric(blobs,lo=0,hi=SIZE):
    if not 0<=lo<hi<=SIZE or lo%4 or hi%4:raise ValueError("Invalid word interval")
    required=[(e,p) for e in (1,2,3) for p in ("stable","hold")]
    if any(k not in blobs or len(blobs[k])!=SIZE for k in required):
        raise ValueError("Six 8MiB snapshots required")
    cam=blobs.get((3,"camera"))
    if cam is not None and len(cam)!=SIZE:raise ValueError("Invalid CAM length")
    values=[blobs[(e,"stable")] for e in (1,2,3)]
    holds=[blobs[(e,"hold")] for e in (1,2,3)]
    rows=[];counts=Counter()
    for off in range(lo,hi,4):
        words=[v[off:off+4] for v in values]
        if not all(words[i]==holds[i][off:off+4] for i in range(3)):continue
        if words[0]==words[1] or words[1]==words[2]:continue
        counts["stable_dynamic_words"]+=1
        camera_changed=cam is not None and words[2]!=cam[off:off+4]
        for fmt,endian in (("float32_be",">"),("float32_le","<")):
            vals=[struct.unpack(endian+"f",w)[0] for w in words]
            if not all(math.isfinite(x) and abs(x)<1000000 for x in vals):continue
            dx=vals[1]-vals[0];dy=vals[2]-vals[1]
            if not all(math.isfinite(x) and 0.0001<=abs(x)<=100000 for x in (dx,dy)):continue
            # Restrict graphics context to exact aligned 8-byte command neighborhood.
            # This is weak evidence, NOT definitive exclusion.
            aligned=off//8*8
            surrounding=[values[i][aligned:aligned+64] for i in range(3)]
            graphics=False
            for block in surrounding:
                ops=[block[j] for j in range(0,len(block)-7,8)]
                if sum(o in OPCODES for o in ops)>=3 and len({o for o in ops if o in OPCODES})>=2 and any(o in STRONG for o in ops):
                    graphics=True;break
            rows.append(dict(offset_hex=f"0x{off:06X}",format=fmt,
                p1=f"{vals[0]:.9g}",p2=f"{vals[1]:.9g}",p3=f"{vals[2]:.9g}",
                delta12=f"{dx:.9g}",delta23=f"{dy:.9g}",
                camera_available=int(cam is not None),camera_changed=int(camera_changed),
                graphics_context=int(graphics),
                review_priority="review" if (not graphics and not camera_changed) else "flagged"))
            counts["float_interpretations"]+=1
    return rows,dict(counts)

def clusters(rows):
    """Potential nearby float32 trio interpretations; do not claim XYZ."""
    index={(int(r["offset_hex"],16),r["format"]):r for r in rows}
    result=[]
    for (off,fmt),a in sorted(index.items()):
        for step in (4,8):
            b=index.get((off+step,fmt));c=index.get((off+2*step,fmt))
            if not (b and c):continue
            flags=[a,b,c]
            result.append(dict(start_hex=f"0x{off:06X}",format=fmt,
                spacing=step,offsets=";".join(f"0x{off+k*step:06X}" for k in range(3)),
                camera_flagged=sum(x["camera_changed"] for x in flags),
                graphics_flagged=sum(x["graphics_context"] for x in flags),
                status="spatial_group_candidate_only"))
    return result

def writecsv(path,rows,fields):
    with path.open("x",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def execute(session,root=Path(".")):
    root=Path(root);blobs=read_capture(session,root)
    words,counts=numeric(blobs)
    groups=clusters(words)
    prefix=root/"output/csv"/f"enemy_freeze_v1_8_{session}"
    paths=[Path(str(prefix)+s) for s in ("_float_candidates.csv","_nearby_groups.csv","_analysis.json")]
    if any(p.exists() for p in paths):raise FileExistsError("v1.8 result already exists")
    writecsv(paths[0],words,["offset_hex","format","p1","p2","p3","delta12","delta23",
                            "camera_available","camera_changed","graphics_context","review_priority"])
    writecsv(paths[1],groups,["start_hex","format","spacing","offsets","camera_flagged","graphics_flagged","status"])
    report=dict(status="full_ram_candidate_only",session=session,bytes_per_snapshot=SIZE,
        captures=len(blobs),counts=counts,nearby_groups=len(groups),
        camera_control_available=(3,"camera") in blobs,
        notes=["Full KSEG0 virtual read of 8MiB; mapping to physical RDRAM not independently verified.",
               "Graphics signature is soft contextual labeling and may miss or overflag content.",
               "Float32 BE/LE numeric changes do not establish enemy coordinates or axes.",
               "CAM marker does not prove camera-only movement; no measured movement vectors.",
               "Fields may be correlated/reused; nearby numeric trios are not validated XYZ."])
    paths[2].write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("session_id");p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args();print(json.dumps(execute(args.session_id,args.root),indent=2,ensure_ascii=False))
