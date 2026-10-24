"""v3.7 axis-aware *candidate* analysis of immutable v3.5 hold summaries.

Diagnostic only: no true position, heading or calibrated displacement available.
"""
import argparse
import csv
import itertools
import json
import math
from pathlib import Path

KINDS=("be_f32","le_f32","be_i32","be_u32")
FIELDS=("session","offset","kind","status","step1","back","step2",
        "first_movement","return_sign_ok","return_close","second_movement",
        "rotation_unchanged","holds_stable","axis_role","candidate","failure_reasons")
CROSS=("offset","kind","evaluated_sessions","passing_sessions","first_response_sessions",
       "second_response_sessions","axis_consistent","decision")
PAIRS=("first_offset","first_kind","second_offset","second_kind","sessions",
       "passing_sessions","min_noncollinearity","decision")
EPS=1e-6
MIN_DET_RATIO=.1
REQUIRED=("session","offset","kind","step1","back","step2",
          "max_hold_mad_ratio","return_error_ratio","rotation_error_ratio",
          "direction_reversed","return_close","rotation_unchanged","holds_stable")

def read_rows(path,sessions):
    with path.open(encoding="utf-8-sig",newline="") as fp:
        reader=csv.DictReader(fp)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError("Expected v3.5 hold_differentials columns")
        rows={}
        for r in reader:
            key=(r["session"],r["offset"],r["kind"])
            if key in rows:raise ValueError("Duplicate "+str(key))
            if r["session"] not in sessions:raise ValueError("Unexpected session "+r["session"])
            if r["kind"] not in KINDS:raise ValueError("Invalid kind "+r["kind"])
            rows[key]=r
    return rows

def audit(row,session,offset,kind):
    output=dict(session=session,offset=offset,kind=kind,
                status="not_evaluable",step1="",back="",step2="",
                first_movement=0,return_sign_ok=0,return_close=0,
                second_movement=0,rotation_unchanged=0,holds_stable=0,
                axis_role="unknown",candidate=0,failure_reasons="missing_v35_row")
    if row is None:return output
    try:
        x,y,z=(float(row[k]) for k in ("step1","back","step2"))
        mad=float(row["max_hold_mad_ratio"])
        rr=float(row["return_error_ratio"])
        rotation=float(row["rotation_error_ratio"])
        flags={k:int(row[k]) for k in
               ("direction_reversed","return_close","rotation_unchanged","holds_stable")}
    except (ValueError,TypeError,KeyError) as ex:
        raise ValueError("Invalid v3.5 record "+str((session,offset,kind))) from ex
    if not all(math.isfinite(v) for v in (x,y,z,mad,rr,rotation)):
        raise ValueError("Nonfinite v3.5 metrics")
    if mad<0 or rr<0 or rotation<0 or any(v not in (0,1) for v in flags.values()):
        raise ValueError("Invalid v3.5 gate/ratio")
    # v3.5 defines noise relative to max(|step1|,|back|,|step2|,EPS).
    scale=max(abs(x),abs(y),abs(z),EPS)
    threshold=max(EPS,10*mad*scale)
    first=int(abs(x)>threshold)
    second=int(abs(z)>threshold)
    # Return/reversal required when first axis changes; if first axis does not
    # change, no significant drift on the return leg is allowed.
    sign=int(x*y<0) if first else int(abs(y)<=threshold)
    close=int(rr<=.1) if first else int(abs(x+y)<=.1*scale)
    rot=int(rotation<=.1)
    stable=int(mad<=.02)
    eligible=int((first or second) and sign and close and rot and stable)
    if first and second:role="both"
    elif first:role="first_only"
    elif second:role="second_only"
    else:role="neither"
    failed=[]
    if not(first or second):failed.append("no_significant_axis")
    if first and not sign:failed.append("first_reversal")
    if not first and not sign:failed.append("return_leg_drift")
    if not close:failed.append("return_to_P0")
    if not rot:failed.append("rotation")
    if not stable:failed.append("hold_stability")
    output.update(status="evaluated",step1=x,back=y,step2=z,
                  first_movement=first,return_sign_ok=sign,return_close=close,
                  second_movement=second,rotation_unchanged=rot,
                  holds_stable=stable,axis_role=role,candidate=eligible,
                  failure_reasons=";".join(failed) if failed else "none")
    return output

def analyze(rows,sessions):
    offsets=[f"0x{a:06X}" for a in range(0x3B30B0,0x3B3100,4)]
    expected={(s,o,k) for s in sessions for o in offsets for k in KINDS}
    if set(rows)-expected:raise ValueError("Rows outside expected grid")
    detail=[audit(rows.get((s,o,k)),s,o,k)
            for s in sessions for o in offsets for k in KINDS]
    idx={(r["session"],r["offset"],r["kind"]):r for r in detail}
    cross=[]
    for o in offsets:
        for k in KINDS:
            group=[idx[s,o,k] for s in sessions]
            passing=sum(r["candidate"] for r in group)
            first=sum(r["first_movement"] for r in group if r["candidate"])
            second=sum(r["second_movement"] for r in group if r["candidate"])
            # Require a reproducible response in at least one direction,
            # not identical role in all sessions (different headings possible).
            consistent=int(passing==len(sessions) and
                           (first==len(sessions) or second==len(sessions)))
            cross.append(dict(offset=o,kind=k,
                              evaluated_sessions=sum(r["status"]=="evaluated" for r in group),
                              passing_sessions=passing,first_response_sessions=first,
                              second_response_sessions=second,
                              axis_consistent=consistent,
                              decision=("axis_candidate_not_validated" if consistent
                                        else "not_supported")))
    eligible=[r for r in cross if r["axis_consistent"]]
    pairs=[]
    # Displacements must span 2D in *each* session. Never pair endian
    # interpretations at the same address.
    for a,b in itertools.combinations(eligible,2):
        if a["offset"]==b["offset"]:continue
        ratios=[]
        for s in sessions:
            p=idx[s,a["offset"],a["kind"]]
            q=idx[s,b["offset"],b["kind"]]
            crossprod=p["step1"]*q["step2"]-q["step1"]*p["step2"]
            denom=abs(p["step1"]*q["step2"])+abs(q["step1"]*p["step2"])
            ratios.append(abs(crossprod)/denom if denom>EPS else 0.)
        passed=sum(x>=MIN_DET_RATIO for x in ratios)
        pairs.append(dict(first_offset=a["offset"],first_kind=a["kind"],
                          second_offset=b["offset"],second_kind=b["kind"],
                          sessions=len(sessions),passing_sessions=passed,
                          min_noncollinearity=min(ratios),
                          decision=("two_axis_candidate_not_validated" if
                                    passed==len(sessions) else "not_supported")))
    summary=dict(schema="spatial_axis_aware_v3_7",sessions=list(sessions),
                 expected_rows=len(detail),
                 evaluated_rows=sum(r["status"]=="evaluated" for r in detail),
                 missing_rows=sum(r["status"]=="not_evaluable" for r in detail),
                 per_session={s:dict(
                     evaluated=sum(r["session"]==s and r["status"]=="evaluated" for r in detail),
                     first_axis=sum(r["session"]==s and r["candidate"] and r["first_movement"] for r in detail),
                     second_axis=sum(r["session"]==s and r["candidate"] and r["second_movement"] for r in detail),
                     candidates=sum(r["session"]==s and r["candidate"] for r in detail))
                     for s in sessions},
                 cross_session_candidates=len(eligible),
                 two_axis_candidates=sum(r["decision"]=="two_axis_candidate_not_validated" for r in pairs),
                 caveat="A statistical movement candidate is NOT a validated Bond coordinate.")
    return detail,cross,pairs,summary

def run(sessions,root=Path(".")):
    if len(sessions)<2 or len(sessions)!=len(set(sessions)):
        raise ValueError("Need at least two distinct sessions")
    folder=Path(root)/"output"/"csv"
    ids="__".join(sessions)
    source=folder/("spatial_v3_5_"+ids+"_hold_differentials.csv")
    detail,cross,pairs,summary=analyze(read_rows(source,set(sessions)),sessions)
    stem=folder/("spatial_v3_7_"+ids)
    paths=[Path(str(stem)+suffix) for suffix in
           ("_axis_responses.csv","_cross_session_axes.csv","_axis_pairs.csv","_summary.json")]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite v3.7 reports")
    for path,cols,content in zip(paths[:3],(FIELDS,CROSS,PAIRS),(detail,cross,pairs)):
        with path.open("x",newline="",encoding="utf-8") as fp:
            writer=csv.DictWriter(fp,fieldnames=cols)
            writer.writeheader()
            writer.writerows(content)
    with paths[-1].open("x",encoding="utf-8") as fp:
        json.dump(summary,fp,indent=2,ensure_ascii=False)
        fp.write("\n")
    return paths,summary

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions",nargs="+")
    parser.add_argument("--root",type=Path,default=Path("."))
    args=parser.parse_args()
    files,result=run(args.sessions,args.root)
    for p in files:print("Wrote",p)
    print("Evaluated",result["evaluated_rows"],"Missing",result["missing_rows"])
    print("Axis candidates",result["cross_session_candidates"],
          "Two-axis candidates",result["two_axis_candidates"])
    print(result["caveat"])
