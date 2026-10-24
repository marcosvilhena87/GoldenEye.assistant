"""v1.6.1: fail-closed absolute-value audit across read-only interventions.
No orientation, unit, or physical meaning is inferred from raw RDRAM windows.
"""
import argparse
import csv
import math
import re
import struct
from pathlib import Path
# Standalone CLI: when called as python tools/analyze_horizontal_v1_6_1.py,
# the repository root is not guaranteed to be on sys.path.
# Keep the eight experimental windows local; do not import from tools package.
OFFSETS = ("0x0D3995", "0x0D3D3D", "0x0D3990", "0x0D3994",
           "0x0D3998", "0x0D3D38", "0x0D3D3C", "0x0D3D40")

PAIRED = ("0x0D3998", "0x0D3D40")
ACTIONS = ("MANUAL_ALIGNMENT", "STATIONARY_TARGET", "STATIONARY_TARGET_AIM_OFF", "FIXED_NO_TARGET", "FIXED_AIM_LEFT", "FIXED_AIM_RIGHT", "FIXED_AIM_CENTER",
           "TURN_LEFT_NO_TARGET", "TURN_RIGHT_NO_TARGET", "TURN_LEFT_AIM_OFF",
           "TURN_RIGHT_AIM_OFF", "REST_AFTER_TURN", "FIXED_AIM_DISABLED",
           "FIXED_AIM_ENABLED", "FIXED_AIM_WITH_TARGET", "FIXED_AIM_NO_TARGET",
           "NEW_SCENE_BASELINE")
FIELDS = ("session","action","offset_hex","first_sample","last_sample","samples",
          "changes","unique_raw","first_raw","last_raw","float32_be_first",
          "float32_be_last","float32_be_delta","float32_be_range",
          "first_to_last_raw_equal","status")
PAIR_FIELDS = ("session","action","samples","paired_transitions","transitions_a",
               "transitions_b","float32_be_finite_pairs","min_b_minus_a",
               "max_b_minus_a","mean_b_minus_a","outliers_from_minus_two_1e4",
               "delta_a","delta_b","direction_a","direction_b","status")

def read(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def be(raw):
    try:
        v = struct.unpack(">f",bytes.fromhex(raw))[0]
        return v if math.isfinite(v) else None
    except (ValueError,struct.error):
        return None

def direction(delta):
    if delta is None: return "not_numeric"
    return "increasing" if delta>0 else "decreasing" if delta<0 else "unchanged"

def audit(markers,timeline,session,termination=None,discontinuities=None):
    if discontinuities: raise ValueError("timeline discontinuity; refuse comparison")
    if termination is not None:
        if len(termination)!=1 or termination[0].get("session")!=session or termination[0].get("reason") not in ("stop","frame_limit") or termination[0].get("active_action")!="NONE":
            raise ValueError("session not cleanly terminated")
    if not markers or not timeline: raise ValueError("empty markers or timeline")
    active=None; intervals=[]
    prev_marker=0
    for m in markers:
        if m.get("session")!=session: raise ValueError("marker session mismatch")
        idx=int(m["sample_index"])
        if idx<=prev_marker: raise ValueError("non-monotonic markers")
        prev_marker=idx
        label=m["label"]
        if label=="STOP":
            if active: raise ValueError("STOP inside interval")
            continue
        phase,sep,action=label.partition("_")
        if not sep or action not in ACTIONS: raise ValueError("invalid marker")
        if phase=="BEGIN":
            if active: raise ValueError("nested actions")
            active=(action,idx,int(m["frame"]))
        elif phase=="END":
            if not active or active[0]!=action or idx<=active[1]: raise ValueError("unmatched end")
            intervals.append((action,active[1],idx,active[2],int(m["frame"])))
            active=None
        else: raise ValueError("invalid phase")
    if active: raise ValueError("incomplete action")
    if not intervals: raise ValueError("no complete interval")
    series={}
    for row in timeline:
        if row.get("session")!=session: raise ValueError("timeline session mismatch")
        key=row.get("offset_hex")
        raw=row.get("raw_hex","")
        if not re.fullmatch(r"0x[0-9A-Fa-f]{6,8}",key or "") or not re.fullmatch(r"[0-9A-Fa-f]{8}",raw):
            raise ValueError("invalid raw sample")
        series.setdefault(key,[]).append((int(row["sample_index"]),int(row["frame"]),raw.upper()))
    if set(OFFSETS)-set(series): raise ValueError("missing required windows")
    for seq in series.values():
        if any(seq[i][0]!=seq[i-1][0]+1 or seq[i][1]!=seq[i-1][1]+1 for i in range(1,len(seq))):
            raise ValueError("timeline discontinuity or duplicate samples")
    rows=[]; pairs=[]
    for action,start,end,start_frame,end_frame in intervals:
        selected={}
        for off,seq in series.items():
            sl=[r for r in seq if start<=r[0]<=end]
            if len(sl)!=end-start+1 or sl[0][1]!=start_frame or sl[-1][1]!=end_frame:
                raise ValueError("missing samples or frame mismatch")
            selected[off]=sl
            vals=[r[2] for r in sl]
            fl=[be(x) for x in vals]
            finite=[x for x in fl if x is not None]
            delta=fl[-1]-fl[0] if fl[0] is not None and fl[-1] is not None else None
            rows.append(dict(session=session,action=action,offset_hex=off,first_sample=start,
                last_sample=end,samples=len(sl),changes=sum(vals[i]!=vals[i-1] for i in range(1,len(vals))),
                unique_raw=len(set(vals)),first_raw=vals[0],last_raw=vals[-1],
                float32_be_first=fl[0],float32_be_last=fl[-1],
                float32_be_delta=delta,float32_be_range=max(finite)-min(finite) if finite else None,
                first_to_last_raw_equal=(vals[0]==vals[-1]),
                status="hypothetical_float32_be_not_validated"))
        aa=selected[PAIRED[0]];bb=selected[PAIRED[1]]
        ta=[r[0] for i,r in enumerate(aa) if i and r[2]!=aa[i-1][2]]
        tb=[r[0] for i,r in enumerate(bb) if i and r[2]!=bb[i-1][2]]
        dd=[be(y[2])-be(x[2]) for x,y in zip(aa,bb) if be(x[2]) is not None and be(y[2]) is not None]
        da=be(aa[-1][2])-be(aa[0][2]) if be(aa[0][2]) is not None and be(aa[-1][2]) is not None else None
        db=be(bb[-1][2])-be(bb[0][2]) if be(bb[0][2]) is not None and be(bb[-1][2]) is not None else None
        pairs.append(dict(session=session,action=action,samples=len(aa),paired_transitions=len(set(ta)&set(tb)),
            transitions_a=len(ta),transitions_b=len(tb),float32_be_finite_pairs=len(dd),
            min_b_minus_a=min(dd) if dd else None,max_b_minus_a=max(dd) if dd else None,
            mean_b_minus_a=sum(dd)/len(dd) if dd else None,
            outliers_from_minus_two_1e4=sum(abs(x+2)>0.0001 for x in dd),
            delta_a=da,delta_b=db,direction_a=direction(da),direction_b=direction(db),
            status="correlation_only_not_heading_or_autoaim_correction"))
    return rows,pairs

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--directory",type=Path,default=Path("output"))
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+",args.session):parser.error("invalid session")
    stem=args.directory/"csv"/f"horizontal_v1_6_1_{args.session}"
    mark=read(Path(str(stem)+"_markers.csv"))
    timeline=read(Path(str(stem)+"_timeline.csv"))
    termination=read(Path(str(stem)+"_termination.csv"))
    disc=read(Path(str(stem)+"_discontinuities.csv"))
    rows,pairs=audit(mark,timeline,args.session,termination,disc)
    outputs=((Path(str(stem)+"_absolute_audit.csv"),FIELDS,rows),
             (Path(str(stem)+"_pair_audit.csv"),PAIR_FIELDS,pairs))
    if any(path.exists() for path,_,_ in outputs):
        raise FileExistsError("Audit already exists; refusing partial overwrite")
    for path,fields,data in outputs:
        with path.open("x",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
        print(f"Wrote {path} rows={len(data)}")
    print("Read-only comparisons. No validated camera heading, weapon heading or auto-aim correction.")

if __name__=="__main__":
    main()
