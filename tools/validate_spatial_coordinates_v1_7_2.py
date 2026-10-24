"""Spatial Coordinate Candidate Validation v1.7.2.

Refines immutable v1.7.1 CSV evidence. No ROM access, writes to game memory,
coordinate claims, or changes to prior reports.
"""
import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

INPUT_FIELDS = ("offset_hex","endianness","delta_left","delta_right",
                "rotation_delta_left","rotation_delta_right",
                "return_error_left","return_error_right",
                "left_pass","right_pass","classification")
FIELDS = INPUT_FIELDS + ("strict_left","strict_right","strict_both",
          "ratio_rotation_left","ratio_rotation_right",
          "ratio_return_left","ratio_return_right","opposite_strict",
          "reasons","pattern_id","cluster_id","status")
GROUP_FIELDS = ("cluster_id","endianness","start_offset","end_offset",
                "members","strict_members","opposite_members","offsets","status")
PATTERN_FIELDS = ("pattern_id","endianness","count","offsets","status")
PROBES = (0x286124,0x286128,0x28612C,0x2863A4,0x2863A8,0x2863AC,
          0x286CEC,0x286CF0,0x286CF4,0x3B2BD4,0x3B2BD8,0x3B2BDC)

def number(raw):
    if raw in (None,""): return None
    try: x=float(raw)
    except (TypeError,ValueError): return None
    return x if math.isfinite(x) else None

def strict(delta,rotation,returned,min_movement=0.01,max_rotation_ratio=0.05,
           max_return_ratio=0.10):
    if any(x is None for x in (delta,rotation,returned)):
        return False,None,None,"missing_or_nonfinite"
    mag=abs(delta)
    if mag<min_movement:
        return False,abs(rotation)/mag if mag else None,abs(returned)/mag if mag else None,"below_min_movement"
    rot=abs(rotation)/mag
    ret=abs(returned)/mag
    if rot>max_rotation_ratio:return False,rot,ret,"rotation_ratio_exceeded"
    if ret>max_return_ratio:return False,rot,ret,"return_ratio_exceeded"
    return True,rot,ret,"strict_pass"

def analyze(rows,min_movement=0.01,max_rotation_ratio=0.05,max_return_ratio=0.10):
    parsed=[]
    seen=set()
    for raw in rows:
        if not set(INPUT_FIELDS).issubset(raw):raise ValueError("missing input fields")
        address=raw["offset_hex"]
        if not re.fullmatch(r"0x[0-9A-Fa-f]{6}",address):raise ValueError("invalid offset")
        offset=int(address,16)
        endian=raw["endianness"]
        if endian not in ("big","little") or offset%4:raise ValueError("unaligned or invalid endianness")
        key=(offset,endian)
        if key in seen:raise ValueError("duplicate input candidate")
        seen.add(key)
        dl=number(raw["delta_left"]);dr=number(raw["delta_right"])
        rl=number(raw["rotation_delta_left"]);rr=number(raw["rotation_delta_right"])
        el=number(raw["return_error_left"]);er=number(raw["return_error_right"])
        lp,lrot,lret,lreason=strict(dl,rl,el,min_movement,max_rotation_ratio,max_return_ratio)
        rp,rrot,rret,rreason=strict(dr,rr,er,min_movement,max_rotation_ratio,max_return_ratio)
        opposite=lp and rp and dl*dr<0
        out={k:raw[k] for k in INPUT_FIELDS}
        out.update(strict_left=lp,strict_right=rp,strict_both=lp and rp,
            ratio_rotation_left=lrot,ratio_rotation_right=rrot,
            ratio_return_left=lret,ratio_return_right=rret,
            opposite_strict=opposite,reasons=f"left:{lreason};right:{rreason}",
            pattern_id="",cluster_id="",status=(
                "strict_opposite_candidate" if opposite else
                "strict_same_sign_candidate" if lp and rp else
                "strict_one_session_candidate" if lp or rp else "rejected_by_strict_filters"))
        parsed.append((offset,endian,dl,dr,rl,rr,el,er,out))
    # Exact signatures are stronger evidence of duplication than rounded similarity,
    # but only show equal observed changes, NOT shared pointer or structure identity.
    signatures=defaultdict(list)
    for offset,endian,dl,dr,rl,rr,el,er,out in parsed:
        if out["strict_left"] or out["strict_right"]:
            signatures[(endian,dl,dr,rl,rr,el,er)].append((offset,out))
    patterns=[]
    pid=0
    for (endian,*_),members in sorted(signatures.items(),key=lambda e:(e[0][0],min(x[0] for x in e[1]))):
        if len(members)<2:continue
        pid+=1
        ident=f"P{pid:04d}"
        for _,r in members:r["pattern_id"]=ident
        patterns.append(dict(pattern_id=ident,endianness=endian,count=len(members),
            offsets=";".join(f"0x{x:06X}" for x,_ in sorted(members)),
            status="same_observed_numeric_pattern_not_proven_alias"))
    # Consecutive 4-byte fields; do not bridge gaps or mix endian interpretations.
    groups=[]
    gid=0
    for endian in ("big","little"):
        ordered=sorted([p for p in parsed if p[1]==endian],key=lambda p:p[0])
        runs=[]
        current=[]
        for p in ordered:
            if current and p[0]!=current[-1][0]+4:
                if len(current)>=2:runs.append(current)
                current=[]
            current.append(p)
        if len(current)>=2:runs.append(current)
        for run in runs:
            gid+=1
            ident=f"G{gid:04d}"
            for p in run:p[-1]["cluster_id"]=ident
            groups.append(dict(cluster_id=ident,endianness=endian,
                start_offset=f"0x{run[0][0]:06X}",end_offset=f"0x{run[-1][0]:06X}",
                members=len(run),strict_members=sum(p[-1]["strict_both"] for p in run),
                opposite_members=sum(p[-1]["opposite_strict"] for p in run),
                offsets=";".join(f"0x{p[0]:06X}" for p in run),
                status="adjacent_words_not_validated_vector"))
    results=[p[-1] for p in parsed]
    results.sort(key=lambda r:(not r["opposite_strict"],not r["strict_both"],
                         not bool(r["cluster_id"]),r["offset_hex"],r["endianness"]))
    return results,groups,patterns

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path,headers,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=headers)
        writer.writeheader();writer.writerows(rows)

def run(root,left,right,min_movement=0.01,max_rotation_ratio=0.05,max_return_ratio=0.10):
    if not all(re.fullmatch(r"[A-Za-z0-9_]+",x) for x in (left,right)):
        raise ValueError("invalid session ID")
    base=root/"output"/"csv"/f"spatial_v1_7_1_{left}_vs_{right}"
    rows=read_csv(Path(str(base)+"_cross_candidates.csv"))
    if not rows:raise ValueError("empty v1.7.1 candidate file")
    result,groups,patterns=analyze(rows,min_movement,max_rotation_ratio,max_return_ratio)
    dest=root/"output"/"csv"/f"spatial_v1_7_2_{left}_vs_{right}"
    files=[(Path(str(dest)+"_strict_candidates.csv"),FIELDS,result),
           (Path(str(dest)+"_adjacent_groups.csv"),GROUP_FIELDS,groups),
           (Path(str(dest)+"_duplicate_patterns.csv"),PATTERN_FIELDS,patterns),
           (Path(str(dest)+"_priority_review.csv"),FIELDS,
              [r for r in result if int(r["offset_hex"],16) in PROBES])]
    if any(path.exists() for path,_,_ in files):
        raise FileExistsError("v1.7.2 results exist; refusing overwrite")
    for path,headers,records in files:write_csv(path,headers,records)
    return files,Counter(r["status"] for r in result)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("left_session");p.add_argument("right_session")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--min-movement",type=float,default=0.01)
    p.add_argument("--max-rotation-ratio",type=float,default=0.05)
    p.add_argument("--max-return-ratio",type=float,default=0.10)
    a=p.parse_args()
    if not all(math.isfinite(x) and x>0 for x in
        (a.min_movement,a.max_rotation_ratio,a.max_return_ratio)):
        p.error("thresholds must be positive and finite")
    files,counts=run(a.root.resolve(),a.left_session,a.right_session,
        a.min_movement,a.max_rotation_ratio,a.max_return_ratio)
    for path,_,records in files:print(f"Wrote {path} rows={len(records)}")
    print("Classification:",dict(counts))
    print("Heuristic only; no proven Bond coordinates or Auto-Aim target.")
if __name__=="__main__":main()
