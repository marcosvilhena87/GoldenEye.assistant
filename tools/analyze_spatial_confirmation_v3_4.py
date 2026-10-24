"""Spatial v3.4 prespecified third-session confirmation; read-only.

The protocol is committed independently of the third-session samples.
No exploration/ranking of unregistered addresses is performed.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES
    from .analyze_spatial_region_v3_1 import get_phases
    from .analyze_spatial_dependency_v2_9 import model
    from .analyze_spatial_shared_source_v2_8 import shifts
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES
    from analyze_spatial_region_v3_1 import get_phases
    from analyze_spatial_dependency_v2_9 import model
    from analyze_spatial_shared_source_v2_8 import shifts

PROTOCOL={
    "protocol":"Spatial Memory Confirmatory Protocol v3.4",
    "discovery_session":"20261024T152944Z_311185",
    "replication_session":"20261024T171358Z_645378",
    "capture_version":"v2.4",
    "phase_order":list(PHASES),
    "pairs":[
       {"left":"0x3B30E0","right":"0x3B30E4","role":"primary"},
       {"left":"0x3B30BC","right":"0x3B30C4","role":"secondary"},
       {"left":"0x3B30D0","right":"0x3B30E0","role":"secondary"},
       {"left":"0x3B30BC","right":"0x3B30C0","role":"diagnostic"},
    ],
    "primary_metric":"accuracy_gain",
    "support_gain_min":0.02,
    "support_logloss_min":0,
    "minimum_primary_supported_phases":7,
    "min_phase_frames":120,
    "null_trials":99,
    "seed_free_null":"fixed evenly-spaced circular rotations",
    "alpha_descriptive":0.05,
    "no_retraining_on_third_session":True,
    "status":"preregistered_candidate_confirmation_not_coordinate_validation"
}
FIELDS=("third_session","pair_role","left","right","phase","train_n","test_n",
        "accuracy_gain","logloss_gain","null_trials","empirical_p_accuracy",
        "null_accuracy_max","phase_support","note")
SUMMARY=("third_session","pair_role","left","right","phases","supported_phases",
         "mean_accuracy_gain","mean_logloss_gain","min_accuracy_gain",
         "decision","protocol_sha256","note")

def canonical_bytes():
    return (json.dumps(PROTOCOL,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("ascii")

def digest():
    return hashlib.sha256(canonical_bytes()).hexdigest()

def score(original,third,train_frames,train_bounds,test_frames,test_bounds,
          trials=None):
    if third in (original,PROTOCOL["replication_session"]):
        raise ValueError("Third session must be new")
    if original!=PROTOCOL["discovery_session"]:
        raise ValueError("Training session does not match protocol")
    null_count=PROTOCOL["null_trials"] if trials is None else trials
    if null_count!=PROTOCOL["null_trials"]:
        raise ValueError("Changing preregistered null trial count is prohibited")
    if any(test_bounds[i+1]-test_bounds[i]<PROTOCOL["min_phase_frames"]
           for i in range(len(PHASES))):
        raise ValueError("Every third-session phase needs >=120 frames")
    a=get_phases(train_frames,train_bounds)
    b=get_phases(test_frames,test_bounds)
    details=[];summaries=[]
    for pair in PROTOCOL["pairs"]:
        left,right=int(pair["left"],16),int(pair["right"],16)
        phase_results=[]
        for phase in PHASES:
            train_x=a[phase][left][0];train_y=a[phase][right][0]
            test_x=b[phase][left][0];test_y=b[phase][right][0]
            observation=model(train_x,train_y,test_x,test_y,alphabet=tuple(range(16)))
            null=[]
            for shift in shifts(len(test_y),null_count):
                rotated=test_y[-shift:]+test_y[:-shift]
                null.append(model(train_x,train_y,test_x,rotated,
                                  alphabet=tuple(range(16)))["accuracy_gain"])
            empirical=(1+sum(v>=observation["accuracy_gain"] for v in null))/(len(null)+1)
            supported=(observation["accuracy_gain"]>=PROTOCOL["support_gain_min"]
                  and observation["logloss_gain"]>PROTOCOL["support_logloss_min"])
            row=dict(third_session=third,pair_role=pair["role"],
                left=pair["left"],right=pair["right"],phase=phase,
                train_n=len(train_x),test_n=len(test_x),
                accuracy_gain=observation["accuracy_gain"],
                logloss_gain=observation["logloss_gain"],
                null_trials=len(null),empirical_p_accuracy=empirical,
                null_accuracy_max=max(null),
                phase_support=int(supported),
                note="exploratory_null_p_not_familywise_controlled")
            details.append(row);phase_results.append(row)
        supported_n=sum(r["phase_support"] for r in phase_results)
        gain=sum(r["accuracy_gain"] for r in phase_results)/len(phase_results)
        loss=sum(r["logloss_gain"] for r in phase_results)/len(phase_results)
        if pair["role"]=="primary":
            decision=("primary_criteria_met" if supported_n>=PROTOCOL["minimum_primary_supported_phases"]
                      and gain>0 and loss>0 else "primary_criteria_not_met")
        else:
            decision="descriptive_only"
        summaries.append(dict(third_session=third,pair_role=pair["role"],
           left=pair["left"],right=pair["right"],phases=len(phase_results),
           supported_phases=supported_n,mean_accuracy_gain=gain,
           mean_logloss_gain=loss,
           min_accuracy_gain=min(r["accuracy_gain"] for r in phase_results),
           decision=decision,protocol_sha256=digest(),
           note="no_coordinate_validation;null_p_unadjusted"))
    return details,summaries

def write_rows(path,columns,records):
    with path.open("x",encoding="utf8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=columns);w.writeheader();w.writerows(records)

def run(third,root):
    original=PROTOCOL["discovery_session"]
    if third in (original,PROTOCOL["replication_session"]):
        raise ValueError("Provide a fresh third-session identifier")
    folder=root/"output"/"csv"
    stem=f"spatial_v3_4_{third}"
    paths=[folder/(stem+"_phase_results.csv"),folder/(stem+"_pair_summary.csv"),
           folder/(stem+"_protocol.json")]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite v3.4 outputs")
    train,b1=load(original,root)
    test,b2=load(third,root)
    details,summaries=score(original,third,train,b1,test,b2)
    write_rows(paths[0],FIELDS,details)
    write_rows(paths[1],SUMMARY,summaries)
    with paths[2].open("x",encoding="utf8") as fh:
        json.dump({"protocol":PROTOCOL,"sha256":digest()},fh,indent=2)
        fh.write("\n")
    return paths,details,summaries

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("third_session",nargs="?")
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--show-protocol",action="store_true")
    args=parser.parse_args()
    if args.show_protocol:
        print(canonical_bytes().decode(),end="")
        print("sha256:",digest())
    else:
        if not args.third_session:parser.error("third_session required unless --show-protocol")
        paths,details,summaries=run(args.third_session,args.root.resolve())
        for p,records in zip(paths[:2],(details,summaries)):
            print(f"Wrote {p} rows={len(records)}")
        print(f"Wrote {paths[2]} protocol SHA256={digest()}")
        print("Confirmatory criteria apply only to preselected pairs; no coordinates proven.")
