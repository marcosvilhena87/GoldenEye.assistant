"""v1.8.3 offline positive motion-control audit. Never validates XYZ automatically."""
import argparse
import csv
import json
from pathlib import Path
from collections import Counter

FIELDS = ("bond_e8","bond_ec","bond_f0","bond_f4","soldier_1_a","soldier_1_b")
PHASES = ("BASELINE","FREEZE_ON","CAMERA_ONLY","SOLDIER_STILL",
          "FREEZE_OFF","SOLDIER_MOVING","SOLDIER_REFROZEN")
def load(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def analyze(sid, root=Path("output/csv")):
    if not sid or any(c in sid for c in "/\\\r\n") or ".." in sid:
        raise ValueError("invalid session")
    prefix = root/("bond_soldier_v1_8_3_"+sid)
    rows=load(Path(str(prefix)+"_timeline.csv"))
    markers=load(Path(str(prefix)+"_markers.csv"))
    ends=load(Path(str(prefix)+"_termination.csv"))
    if not rows:
        raise ValueError("no timeline")
    by_frame={}
    aliases=[]
    for row in rows:
        if row["session"] != sid or row["field"] not in FIELDS:
            raise ValueError("unexpected row")
        n=int(row["frame"])
        part=by_frame.setdefault(n,{})
        if row["field"] in part:
            raise ValueError("duplicate field")
        part[row["field"]]=row
        if row["alias_equal"]!="1":
            aliases.append([n,row["field"]])
    allframes=sorted(by_frame)
    incomplete=[{"frame":n,"missing":sorted(set(FIELDS)-set(by_frame[n]))}
                for n in allframes if set(by_frame[n])!=set(FIELDS)]
    if any(x["frame"]!=allframes[-1] for x in incomplete):
        raise ValueError("incomplete interior frame: "+str(incomplete[:3]))
    if incomplete: del by_frame[allframes[-1]]
    frames=sorted(by_frame)
    gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
    changes=[]
    for a,b in zip(frames,frames[1:]):
        if b!=a+1: continue
        for field in FIELDS:
            x,y=by_frame[a][field],by_frame[b][field]
            if x["kseg0_hex"]!=y["kseg0_hex"]:
                changes.append({"frame":b,"phase":y["phase"],"field":field,
                                "old":x["kseg0_hex"],"new":y["kseg0_hex"]})
    phases={}
    for n in frames:
        p=by_frame[n]["bond_ec"]["phase"]
        phases.setdefault(p,[]).append(n)
    table=[]
    counts=Counter((e["phase"],e["field"]) for e in changes)
    for p,nums in phases.items():
        for field in FIELDS:
            values={by_frame[n][field]["kseg0_hex"] for n in nums}
            table.append({"phase":p,"field":field,"frames":len(nums),
                          "distinct_raw_values":len(values),
                          "changes":counts[(p,field)],
                          "stable_raw":len(values)==1})
    clean=bool(ends and ends[-1].get("reason")=="stop" and not incomplete and not gaps)
    def phase_fields(p):
        return {x["field"]:x for x in table if x["phase"]==p}
    moving=phase_fields("SOLDIER_MOVING")
    before=phase_fields("SOLDIER_STILL")
    after=phase_fields("SOLDIER_REFROZEN")
    freeze=phase_fields("FREEZE_ON")
    soldier=("soldier_1_a","soldier_1_b")
    control_exists=bool(before and moving and after and freeze)
    candidate_change=bool(moving and any(moving[f]["changes"]>0 for f in soldier))
    stable_controls=bool(control_exists and all(
        group[f]["stable_raw"] for group in (before,after,freeze) for f in soldier))
    interpretation=("candidate_motion_response_observed" if
        clean and control_exists and candidate_change and stable_controls
        else "insufficient_positive_motion_control")
    return {"protocol":"bond_soldier_positive_motion_v1_8_3",
        "session":sid,"frames":len(frames),"capture_complete":clean,
        "termination":ends,"incomplete_frames":incomplete,
        "timeline_gaps":gaps,"alias_mismatches":aliases,
        "markers":[{"frame":int(m["frame"]),"label":m["label"]} for m in markers],
        "phase_stats":table,"changes_by_phase_field":[
            {"phase":p,"field":f,"count":n} for (p,f),n in sorted(counts.items())],
        "positive_control":{"all_required_phases_present":control_exists,
           "soldier_raw_changes_during_movement_phase":candidate_change,
           "soldier_raw_stable_during_freeze_controls":stable_controls,
           "classification":interpretation},
        "visual_soldier_movement_independently_verified":False,
        "soldier_xyz_validated":False,"bond_xyz_validated":False,
        "canonical_symbol_promoted":False,
        "limitations":["Phase labels are operator annotations, not proof that Freeze or movement occurred.",
           "Camera and Bond must be stationary during soldier motion.",
           "Raw four-byte words are untyped candidates, regardless of float interpretation.",
           "Same soldier identity and physical movement require independent visual verification.",
           "Movement-associated bytes do not by themselves prove world coordinates."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("output/csv"))
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    report=analyze(args.session,args.root)
    out=args.output or args.root/("bond_soldier_v1_8_3_"+args.session+"_analysis.json")
    if out.exists(): raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Soldier v1.8.3:",out,"frames:",report["frames"],
          "complete:",report["capture_complete"],
          "classification:",report["positive_control"]["classification"])
if __name__=="__main__": main()
