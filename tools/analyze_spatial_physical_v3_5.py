"""v3.5: physical displacement *candidate* audit for verified v2.4 sessions.

Runs retrospective movement/hold tests on decoded values. Does not know Bond's
ground-truth world coordinates, distance or angles: never validates an XYZ field.
"""
import argparse
import csv
import math
import statistics
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES, START, END, decode
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES, START, END, decode

HOLDS=("P0_HOLD","P1_HOLD","P0_RETURN_HOLD","P0_ROTATED_HOLD","P2_HOLD")
KINDS=("be_f32","le_f32","be_i32","be_u32")
OFFSETS=tuple(range(START,END-2,4))
MIN_HOLD=120
TAIL=120
EPS=1e-6
FIELDS=("session","offset","kind","p0","p1","p0_return","p0_rotated","p2",
        "step1","back","step2","return_error_ratio","rotation_error_ratio",
        "max_hold_mad_ratio","direction_reversed","return_close",
        "rotation_unchanged","holds_stable","second_step_nonzero","candidate",
        "note")
SUMMARY=("offset","kind","sessions","passed","failed","decision",
         "min_step_magnitude","worst_return_error_ratio","worst_rotation_error_ratio",
         "worst_hold_mad_ratio","note")
PAIR=("session","first_offset","second_offset","first_kind","second_kind",
      "first_step1","second_step1","first_step2","second_step2",
      "noncollinear_increments","note")

def median_mad(vals):
    if not vals or not all(math.isfinite(x) for x in vals):return None
    mid=statistics.median(vals)
    return mid,statistics.median(abs(x-mid) for x in vals)

def sample_session(session,frames,bounds,tail=TAIL):
    if len(bounds)!=10 or any(b<=a for a,b in zip(bounds,bounds[1:])):
        raise ValueError("Invalid phase boundaries")
    if tail<10:raise ValueError("tail must be >=10")
    hold_ids={}
    for phase in HOLDS:
        i=PHASES.index(phase)
        if bounds[i+1]-bounds[i]<max(tail,MIN_HOLD):
            raise ValueError("Hold too short: "+phase)
        hold_ids[phase]=range(bounds[i+1]-tail,bounds[i+1])
    rows=[]
    for addr in OFFSETS:
        for kind in KINDS:
            stats={}
            for phase,ids in hold_ids.items():
                vals=[decode(bytes(frames[f][addr+j] for j in range(4)),kind)
                      for f in ids]
                stats[phase]=median_mad(vals)
            if any(x is None for x in stats.values()):continue
            p0,p1,ret,rot,p2=(stats[p][0] for p in HOLDS)
            step=p1-p0;back=ret-p1;step2=p2-rot
            # Ratios are meaningful only when step exceeds both absolute floor
            # and observed hold noise. Constant/near-constant bytes are rejected.
            noise=max(stats[p][1] for p in HOLDS)
            scale=max(abs(step),abs(back),abs(step2),EPS)
            meaningful=(abs(step)>max(EPS,noise*10)
                        and abs(back)>max(EPS,noise*10)
                        and abs(step2)>max(EPS,noise*10))
            rr=abs(ret-p0)/scale
            rot_ratio=abs(rot-ret)/scale
            mad_ratio=noise/scale
            reverse=step*back<0
            close=rr<=.1
            stationary=rot_ratio<=.1
            stable=mad_ratio<=.02
            accepted=all((meaningful,reverse,close,stationary,stable))
            rows.append(dict(session=session,offset=f"0x{addr:06X}",kind=kind,
                p0=p0,p1=p1,p0_return=ret,p0_rotated=rot,p2=p2,
                step1=step,back=back,step2=step2,
                return_error_ratio=rr,rotation_error_ratio=rot_ratio,
                max_hold_mad_ratio=mad_ratio,direction_reversed=int(reverse),
                return_close=int(close),rotation_unchanged=int(stationary),
                holds_stable=int(stable),second_step_nonzero=int(meaningful),
                candidate=int(accepted),
                note="physical_position_candidate_not_ground_truth"))
    return rows

def summarize(groups):
    sessions={r["session"] for rows in groups for r in rows}
    if len(sessions)!=len(groups):raise ValueError("Sessions must be distinct")
    by_key={}
    for rows in groups:
        for r in rows:
            key=(r["offset"],r["kind"])
            by_key.setdefault(key,[]).append(r)
    result=[]
    for (offset,kind),rows in sorted(by_key.items()):
        good=sum(int(r["candidate"]) for r in rows)
        complete=len(rows)==len(groups)
        passed=complete and good==len(groups)
        result.append(dict(offset=offset,kind=kind,sessions=len(rows),
            passed=good,failed=len(groups)-good,decision=(
                "cross_session_candidate" if passed else "not_supported"),
            min_step_magnitude=min(abs(r["step1"]) for r in rows),
            worst_return_error_ratio=max(r["return_error_ratio"] for r in rows),
            worst_rotation_error_ratio=max(r["rotation_error_ratio"] for r in rows),
            worst_hold_mad_ratio=max(r["max_hold_mad_ratio"] for r in rows),
            note="not_physical_coordinate_validation"))
    return result

def paired_axes(groups,summary):
    # Only pairs that pass individually in all sessions. Different underlying
    # address required, and both directional displacements must be noncollinear
    # across step 1 vs step 2. No heading angles or spatial calibration given.
    passed=[(r["offset"],r["kind"]) for r in summary
            if r["decision"]=="cross_session_candidate"]
    index={r["session"]:{(x["offset"],x["kind"]):x for x in rows}
           for rows in groups for r in rows}
    result=[]
    for i,(a,ak) in enumerate(passed):
        for b,bk in passed[i+1:]:
            if a==b:continue
            for session,records in index.items():
                x,y=records[(a,ak)],records[(b,bk)]
                det=x["step1"]*y["step2"]-y["step1"]*x["step2"]
                magnitude=abs(x["step1"]*y["step2"])+abs(y["step1"]*x["step2"])
                ok=magnitude>EPS and abs(det)/magnitude>=.1
                result.append(dict(session=session,first_offset=a,
                    second_offset=b,first_kind=ak,second_kind=bk,
                    first_step1=x["step1"],second_step1=y["step1"],
                    first_step2=x["step2"],second_step2=y["step2"],
                    noncollinear_increments=int(ok),
                    note="geometry_proxy_requires_ground_truth"))
    return result

def run(sessions,root,tail=TAIL):
    if len(sessions)<2 or len(set(sessions))!=len(sessions):
        raise ValueError("At least two distinct sessions required")
    groups=[]
    for session in sessions:
        frames,bounds=load(session,root)
        groups.append(sample_session(session,frames,bounds,tail))
    summary=summarize(groups)
    axes=paired_axes(groups,summary)
    folder=root/"output"/"csv"
    stem="spatial_v3_5_"+"__".join(sessions)
    outputs=(("_hold_differentials.csv",FIELDS,
              [row for group in groups for row in group]),
             ("_cross_session.csv",SUMMARY,summary),
             ("_axis_pairs.csv",PAIR,axes))
    paths=[folder/(stem+s) for s,_,_ in outputs]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite v3.5 outputs")
    for path,(_,cols,rows) in zip(paths,outputs):
        with path.open("x",encoding="utf8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=cols);writer.writeheader()
            writer.writerows(rows)
    return paths,[rows for _,_,rows in outputs]

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("sessions",nargs="+")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--tail",type=int,default=TAIL)
    args=p.parse_args()
    paths,rows=run(args.sessions,args.root.resolve(),args.tail)
    for path,data in zip(paths,rows):print(f"Wrote {path} rows={len(data)}")
    print("No validated physical coordinates: direct positional ground truth absent.")
