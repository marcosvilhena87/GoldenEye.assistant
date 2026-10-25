"""Offline RDRAM candidate scan for Soldier #1 v1.8.5. Never assigns X/Z automatically."""
import argparse
import csv
import json
import math
import struct
from pathlib import Path

LABELS=("BASELINE","BOND_ROTATE","BOND_MOVE","SOLDIER_MOVE","SOLDIER_FREEZE")
ANCHORS=(0x0D33EC,0x0D33F4,0x06D248,0x06D250)
OLD=(0x20F594,0x20F5AC)
def words(data,endian=">"):
    for offset in range(0,len(data)-3,4):
        value=struct.unpack_from(endian+"f",data,offset)[0]
        yield offset,value
def load_manifest(sid,root):
    path=root/"csv"/f"soldier_coordinate_v1_8_5_{sid}_manifest.csv"
    with path.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    labels={}
    for row in rows:
        if row["session"]!=sid or row["label"] in labels:raise ValueError("bad manifest")
        label=row["label"]
        if label not in LABELS and label!="NEW_SAVE":raise ValueError("unknown label")
        p=Path(row["path"])
        # trust only expected filenames in archive/; refuse relative traversal
        expected=f"soldier_coordinate_v1_8_5_{sid}_{label}.bin"
        if p.name!=expected:raise ValueError("bad snapshot path")
        location=root/"archive"/expected
        size=int(row["size"])
        if row["domain"]!="RDRAM" or size!=8388608:raise ValueError("invalid domain/size")
        data=location.read_bytes()
        if len(data)!=size:raise ValueError("truncated snapshot "+label)
        labels[label]=data
    return labels
def scan(snapshots,limit=150,near=5000.0):
    missing=[x for x in LABELS if x not in snapshots]
    if missing:raise ValueError("missing controlled captures "+",".join(missing))
    base,rot,bond,moving,frozen=(snapshots[x] for x in LABELS)
    if len({len(x) for x in (base,rot,bond,moving,frozen)})!=1:raise ValueError("sizes differ")
    anchors=[]
    for offset in ANCHORS:
        for fmt in (">f","<f"):
            x=struct.unpack_from(fmt,base,offset)[0]
            if math.isfinite(x) and 1.0<abs(x)<1e7:anchors.append({"offset":f"0x{offset:06X}","format":fmt,"value":x})
    candidates=[]
    for offset in range(0,len(base)-3,4):
        b=base[offset:offset+4];r=rot[offset:offset+4];q=bond[offset:offset+4];m=moving[offset:offset+4];f=frozen[offset:offset+4]
        # Restrictive negative controls; movement detected independently.
        if m==r or b!=r:continue
        # Require stable read in frozen snapshot relative to moving? 
        # A snapshot is a single timepoint, so cannot establish frozen stability here.
        for fmt in (">f","<f"):
            x=struct.unpack(fmt,b)[0];y=struct.unpack(fmt,m)[0]
            if not all(math.isfinite(v) and 1<abs(v)<1e7 for v in (x,y)):continue
            diff=abs(y-x)
            if diff<0.01 or diff>1e5:continue
            nearest=min((abs(x-a["value"]) for a in anchors),default=None)
            proximal=nearest is not None and nearest<=near
            score=3+(2 if q==b else 0)+(1 if f==m else 0)+(2 if proximal else 0)
            candidates.append({"offset_hex":f"0x{offset:06X}","decode":fmt,"baseline":x,
                "soldier_move":y,"delta":y-x,"freeze_snapshot":struct.unpack(fmt,f)[0],
                "bond_move_unchanged":q==b,"nearest_bond_anchor_distance":nearest,
                "numeric_proximity_filter":proximal,"score":score,
                "old_offset":offset in OLD})
    candidates.sort(key=lambda c:(-c["score"],c["nearest_bond_anchor_distance"] if c["nearest_bond_anchor_distance"] is not None else float("inf"),c["offset_hex"]))
    return {"status":"candidates_only","candidate_count":len(candidates),"top_candidates":candidates[:limit],
        "anchor_hypotheses":anchors,"snapshot_labels":list(snapshots),
        "unvalidated":["Bond reference is not independently established position","Single snapshots do not prove stationary/frozen state",
           "Integer/unaligned/offset-translated structures may be missed","A changed field may be animation, AI or global state","X/Z, Soldier #1 identity, cross-save persistence and world coordinates remain unvalidated"]}
def analyze(sid,root=Path("output"),limit=150,near=5000.):
    if not sid or any(x in sid for x in ("/","\\","..","\n")):raise ValueError("unsafe SID")
    if not (1<=limit<=10000) or not (0<near<=1e7):raise ValueError("unsafe params")
    snap=load_manifest(sid,root)
    report=scan(snap,limit,near)
    report["session"]=sid
    report["new_save_captured"]="NEW_SAVE" in snap
    report["new_save_validation"]="not_evaluated_requires_paired_controlled_session" 
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("output"))
    p.add_argument("--limit",type=int,default=150)
    p.add_argument("--near",type=float,default=5000.)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    report=analyze(a.session,a.root,a.limit,a.near)
    out=a.output or a.root/"csv"/f"soldier_coordinate_v1_8_5_{a.session}_analysis.json"
    if out.exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Soldier v1.8.5:",out,"candidates:",report["candidate_count"],"top:",len(report["top_candidates"]))
if __name__=="__main__":main()
