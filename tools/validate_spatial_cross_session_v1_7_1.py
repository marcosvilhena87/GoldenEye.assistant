"""Cross-session spatial v1.7.1: full-snapshot read-only candidate audit.

Scan all aligned RDRAM words for both float32 endian hypotheses, with no Top-100
input or output cutoff. Opposite signs are descriptive, never semantic proof.
"""
import argparse
import csv
import math
import mmap
import re
import struct
from contextlib import ExitStack
from pathlib import Path

try:
    from tools.analyze_spatial_v1_7 import read, validate_manifest
except ModuleNotFoundError:
    from analyze_spatial_v1_7 import read, validate_manifest

SIZE = 8388608
PROBES = (0x3B2BD4, 0x3B2BD8, 0x3B2BDC,
          0x1F1E88, 0x1F1E8C, 0x1F1E90, 0x05FCB4, 0x05FCD4, 0x2EBCE4)
FIELDS = ("offset_hex","endianness","baseline_left","moved_left","returned_left",
          "rotated_left","baseline_right","moved_right","returned_right",
          "rotated_right","delta_left","delta_right","rotation_delta_left",
          "rotation_delta_right","return_error_left","return_error_right",
          "opposite_sign","left_pass","right_pass","classification",
          "candidate_only")

def load_paths(root, sid, movement, rotation):
    if not re.fullmatch(r"[A-Za-z0-9_]+", sid):
        raise ValueError("invalid session")
    stem = root / "output" / "csv" / ("spatial_v1_7_" + sid)
    def part(suffix):
        return read(Path(str(stem) + suffix))
    mapping = validate_manifest(part("_snapshots.csv"),part("_markers.csv"),
        part("_termination.csv"),part("_discontinuities.csv"),sid,root)
    labels = ("BOND_BASELINE",movement,"BOND_RETURN",rotation)
    if not all(x in mapping for x in labels):
        raise ValueError(f"incomplete session {sid}; required labels: {labels}")
    return [mapping[x] for x in labels]

def decoded(mm, i, end):
    val = struct.unpack_from((">" if end=="big" else "<") + "f", mm, i)[0]
    return val if math.isfinite(val) and abs(val)<=1e6 else None

def evaluate(values):
    a,b,r,t=values
    if any(x is None for x in values):
        return False,None,None,None,"nonfinite_or_out_of_range"
    delta=b-a
    turn=t-a
    err=abs(r-a)
    changing=0.00001<abs(delta)<100000
    stable_turn=abs(turn)<=max(0.001,abs(delta)*0.05)
    stable_return=err<=max(0.001,abs(delta)*0.10)
    ok=changing and stable_turn and stable_return
    return ok,delta,turn,err,("pass" if ok else "fails_movement_or_stability_filters")

def row_at(mm, index, end):
    vals=[tuple(decoded(buf,index,end) for buf in session) for session in mm]
    lp,dl,tl,el,_=evaluate(vals[0])
    rp,dr,tr,er,_=evaluate(vals[1])
    opposite=(dl*dr<0) if dl is not None and dr is not None and dl!=0 and dr!=0 else None
    if lp and rp:
        category="opposite_sign_unverified" if opposite else "same_sign_unverified"
    elif lp or rp:
        category="one_session_only_unverified"
    else:
        category="fails_filters_or_inconclusive"
    return dict(offset_hex=f"0x{index:06X}",endianness=end,
        baseline_left=vals[0][0],moved_left=vals[0][1],
        returned_left=vals[0][2],rotated_left=vals[0][3],
        baseline_right=vals[1][0],moved_right=vals[1][1],
        returned_right=vals[1][2],rotated_right=vals[1][3],
        delta_left=dl,delta_right=dr,rotation_delta_left=tl,
        rotation_delta_right=tr,return_error_left=el,return_error_right=er,
        opposite_sign=opposite,left_pass=lp,right_pass=rp,
        classification=category,candidate_only=True)

def scan(mm, probe_offsets=PROBES):
    if len(mm)!=2 or any(len(session)!=4 for session in mm):
        raise ValueError("expected 2 sessions with 4 snapshots each")
    if any(len(buf)!=SIZE for session in mm for buf in session):
        raise ValueError("unexpected memory dump length")
    candidate_rows=[]
    probes=[]
    counts={"both":0,"opposite":0,"same":0,"one":0,"checked_aligned_words":SIZE//4}
    for i in range(0,SIZE,4):
        # Skip when a field has no raw change on both movement snapshots.
        moving=(mm[0][0][i:i+4]!=mm[0][1][i:i+4] or
                mm[1][0][i:i+4]!=mm[1][1][i:i+4])
        if not moving and i not in probe_offsets:
            continue
        for end in ("big","little"):
            row=row_at(mm,i,end)
            if i in probe_offsets:
                probes.append(row)
            if not (row["left_pass"] or row["right_pass"]):
                continue
            candidate_rows.append(row)
            if row["left_pass"] and row["right_pass"]:
                counts["both"]+=1
                counts["opposite" if row["opposite_sign"] else "same"]+=1
            else:
                counts["one"]+=1
    candidate_rows.sort(key=lambda r:(not (r["left_pass"] and r["right_pass"]),
        not (r["opposite_sign"] is True),r["offset_hex"],r["endianness"]))
    return candidate_rows,probes,counts

def write_csv_exclusive(path,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(rows)

def run(root,left_sid,right_sid):
    l=load_paths(root,left_sid,"BOND_MOVE_LEFT","BOND_ROTATE_LEFT")
    r=load_paths(root,right_sid,"BOND_MOVE_RIGHT","BOND_ROTATE_RIGHT")
    name=f"spatial_v1_7_1_{left_sid}_vs_{right_sid}"
    prefix=root/"output"/"csv"/name
    candidate=Path(str(prefix)+"_cross_candidates.csv")
    probes=Path(str(prefix)+"_priority_probes.csv")
    if candidate.exists() or probes.exists():
        raise FileExistsError("Output already exists; refuse overwrite")
    with ExitStack() as stack:
        mm=[]
        for session in (l,r):
            buffers=[]
            for p in session:
                f=stack.enter_context(p.open("rb"))
                buffers.append(stack.enter_context(mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)))
            mm.append(buffers)
        candidates,priority,counts=scan(mm)
    # Both outputs validated before opening either.
    write_csv_exclusive(candidate,candidates)
    write_csv_exclusive(probes,priority)
    return candidate,probes,counts

def main():
    p=argparse.ArgumentParser()
    p.add_argument("left_session")
    p.add_argument("right_session")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    candidates,probes,counts=run(a.root.resolve(),a.left_session,a.right_session)
    print("Cross-session candidates:",candidates,"rows",counts["both"]+counts["one"])
    print("Priority probes:",probes)
    print("Shared candidates:",counts["both"],"opposite:",counts["opposite"],
          "same:",counts["same"],"one session only:",counts["one"])
    print("No validated positions or geometry; opposite signs do not prove Bond coordinates.")

if __name__=="__main__":
    main()
