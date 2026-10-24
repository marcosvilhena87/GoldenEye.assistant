"""Spatial Data Type Validation v1.7.3: RAW/float/int evidence, no addresses assumed.

Reads the original 8 RDRAM snapshots using the validated v1.7.1 manifest.
Audits union of v1.7.2 candidates and historically prioritized addresses.
Produces immutable per-snapshot and per-session CSVs; no writes to game memory.
"""
import argparse,csv,math,struct,re
from pathlib import Path
from contextlib import ExitStack
try:
    from tools.validate_spatial_cross_session_v1_7_1 import load_paths
except ModuleNotFoundError:
    from validate_spatial_cross_session_v1_7_1 import load_paths

PROBES=(0x2EC5D4,0x2E1480,0x285264,0x286124,0x286128,0x28612C,
        0x2863A4,0x2863A8,0x2863AC,0x286CEC,0x286CF0,0x286CF4,
        0x3B2BD4,0x3B2BD8,0x3B2BDC)
LABELS=(("BOND_BASELINE","BOND_MOVE_LEFT","BOND_RETURN","BOND_ROTATE_LEFT"),
        ("BOND_BASELINE","BOND_MOVE_RIGHT","BOND_RETURN","BOND_ROTATE_RIGHT"))
SNAP_FIELDS=("session","label","offset_hex","raw_hex","float_be","float_le",
             "int32_be","int32_le","uint32_be","uint32_le",
             "float_be_kind","float_le_kind")
AUDIT_FIELDS=("offset_hex","session","raw_baseline","raw_moved","raw_return",
              "raw_rotation","changed_bytes_move","changed_bytes_return",
              "changed_bytes_rotation","raw_return_equal","raw_rotation_equal",
              "float_be_delta","float_le_delta","int32_be_delta","int32_le_delta",
              "uint32_be_delta","uint32_le_delta","float_be_kinds",
              "float_le_kinds","int32_be_return_equal","int32_le_return_equal",
              "classification","status")

def float_kind(raw,end):
    bits=int.from_bytes(raw,end)
    exponent=(bits>>23)&255
    fraction=bits&0x7fffff
    if exponent==255:return "nan" if fraction else "infinity"
    if exponent==0:return "subnormal" if fraction else "zero"
    return "normal"

def interpret(raw):
    if len(raw)!=4:raise ValueError("four bytes required")
    data={}
    for name,end in (("be","big"),("le","little")):
        fmt=">" if end=="big" else "<"
        val=struct.unpack(fmt+"f",raw)[0]
        data["float_"+name]=val if math.isfinite(val) else None
        data["float_"+name+"_kind"]=float_kind(raw,end)
        data["int32_"+name]=int.from_bytes(raw,end,signed=True)
        data["uint32_"+name]=int.from_bytes(raw,end,signed=False)
    return data

def count_changed(a,b):
    return sum(x!=y for x,y in zip(a,b))

def delta(x,y):
    return y-x if x is not None and y is not None else None

def audit_four(raws,session,offset):
    if len(raws)!=4:raise ValueError("four snapshots required")
    data=[interpret(x) for x in raws]
    base,moved,returned,rotation=raws
    kinds_be=[x["float_be_kind"] for x in data]
    kinds_le=[x["float_le_kind"] for x in data]
    suspect=any(x in ("subnormal","nan","infinity") for x in kinds_be+kinds_le)
    stable_return=base==returned
    stable_rotation=base==rotation
    if stable_return and stable_rotation and base!=moved:
        cls="raw_motion_association_unverified"
    elif not stable_return:
        cls="raw_nonreturn_or_inconclusive"
    elif not stable_rotation:
        cls="raw_rotation_sensitive_or_inconclusive"
    else:
        cls="raw_stable_or_inconclusive"
    return dict(offset_hex=f"0x{offset:06X}",session=session,
        raw_baseline=base.hex().upper(),raw_moved=moved.hex().upper(),
        raw_return=returned.hex().upper(),raw_rotation=rotation.hex().upper(),
        changed_bytes_move=count_changed(base,moved),
        changed_bytes_return=count_changed(base,returned),
        changed_bytes_rotation=count_changed(base,rotation),
        raw_return_equal=stable_return,raw_rotation_equal=stable_rotation,
        float_be_delta=delta(data[0]["float_be"],data[1]["float_be"]),
        float_le_delta=delta(data[0]["float_le"],data[1]["float_le"]),
        int32_be_delta=delta(data[0]["int32_be"],data[1]["int32_be"]),
        int32_le_delta=delta(data[0]["int32_le"],data[1]["int32_le"]),
        uint32_be_delta=delta(data[0]["uint32_be"],data[1]["uint32_be"]),
        uint32_le_delta=delta(data[0]["uint32_le"],data[1]["uint32_le"]),
        float_be_kinds=";".join(kinds_be),float_le_kinds=";".join(kinds_le),
        int32_be_return_equal=data[0]["int32_be"]==data[2]["int32_be"],
        int32_le_return_equal=data[0]["int32_le"]==data[2]["int32_le"],
        classification=cls,
        status="representation_ambiguous_subnormal_or_nonfinite" if suspect else "representation_not_validated")

def offsets_from_candidates(path):
    with path.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows or "offset_hex" not in rows[0]:raise ValueError("invalid v1.7.2 source CSV")
    offsets=set(PROBES)
    for row in rows:
        value=row["offset_hex"]
        if not re.fullmatch(r"0x[0-9A-Fa-f]{6}",value):raise ValueError("invalid candidate offset")
        address=int(value,16)
        if address%4 or address+4>8388608:raise ValueError("out-of-bounds or unaligned candidate")
        offsets.add(address)
    return sorted(offsets)

def write(path,fields,rows):
    with path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def run(root,left,right):
    if not all(re.fullmatch(r"[A-Za-z0-9_]+",s) for s in (left,right)):
        raise ValueError("invalid session id")
    source=root/"output"/"csv"/f"spatial_v1_7_2_{left}_vs_{right}_strict_candidates.csv"
    offsets=offsets_from_candidates(source)
    paths=[load_paths(root,left,"BOND_MOVE_LEFT","BOND_ROTATE_LEFT"),
           load_paths(root,right,"BOND_MOVE_RIGHT","BOND_ROTATE_RIGHT")]
    prefix=root/"output"/"csv"/f"spatial_v1_7_3_{left}_vs_{right}"
    detail=Path(str(prefix)+"_raw_values.csv")
    audit=Path(str(prefix)+"_type_audit.csv")
    priority=Path(str(prefix)+"_priority_review.csv")
    if any(p.exists() for p in (detail,audit,priority)):
        raise FileExistsError("v1.7.3 output exists; refusing overwrite")
    details=[];audits=[];priorities=[]
    with ExitStack() as stack:
        handles=[[stack.enter_context(p.open("rb")) for p in ses] for ses in paths]
        for offset in offsets:
            for session_idx,sid in enumerate((left,right)):
                raw=[]
                for h in handles[session_idx]:
                    h.seek(offset)
                    value=h.read(4)
                    if len(value)!=4:raise ValueError("incomplete snapshot")
                    raw.append(value)
                for label,value in zip(LABELS[session_idx],raw):
                    details.append(dict(session=sid,label=label,offset_hex=f"0x{offset:06X}",
                        raw_hex=value.hex().upper(),**interpret(value)))
                row=audit_four(raw,sid,offset)
                audits.append(row)
                if offset in PROBES:priorities.append(row)
    write(detail,SNAP_FIELDS,details)
    write(audit,AUDIT_FIELDS,audits)
    write(priority,AUDIT_FIELDS,priorities)
    return detail,audit,priority,len(offsets)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("left_session");p.add_argument("right_session")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    details,audit,priority,n=run(a.root.resolve(),a.left_session,a.right_session)
    print(f"Audited offsets={n} snapshots=8")
    print("RAW:",details)
    print("Type audit:",audit)
    print("Priority:",priority)
    print("No validated data type, coordinates, soldier identities or Auto-Aim correction.")

if __name__=="__main__":main()
