"""v3.0 independent replication against the v2.4 read-only capture protocol.

The second capture must be independently collected; this module never reads
emulator memory or promotes candidate addresses.
"""
import argparse
import csv
from itertools import combinations
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES, START, END
    from .analyze_spatial_structure_v2_6 import BASES
    from .analyze_spatial_shared_source_v2_8 import block_flags,compare_flags
    from .analyze_spatial_dependency_v2_9 import representations,model
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES, START, END
    from analyze_spatial_structure_v2_6 import BASES
    from analyze_spatial_shared_source_v2_8 import block_flags,compare_flags
    from analyze_spatial_dependency_v2_9 import representations,model

# Predeclared negative comparisons, not discovered or validated fields.
CONTROLS=((START,START+4),(START+8,START+12),(START+16,START+20))
PAIRS=((BASES[0],BASES[1]),)+CONTROLS
FIELDS=("training_session","replication_session","phase","left","right","pair_type",
        "feature","train_frames","test_frames","baseline_accuracy",
        "conditional_accuracy","accuracy_gain","baseline_logloss",
        "conditional_logloss","logloss_gain","seen_fraction",
        "train_sync_given_either","test_sync_given_either","train_phi",
        "test_phi","note")
SUMMARY=("training_session","replication_session","left","right","pair_type",
         "mean_test_accuracy_gain_mask","min_test_accuracy_gain_mask",
         "mean_test_logloss_gain_mask","mean_test_sync","phases","note")

def features(frames,boundaries,bases):
    result={}
    for i,phase in enumerate(PHASES):
        idx=range(boundaries[i],boundaries[i+1])
        words={base:[tuple(frames[f][base+j] for j in range(4)) for f in idx] for base in bases}
        if len(words[bases[0]])<12:raise ValueError("Short phase: "+phase)
        masks={base:block_flags(values)[0] for base,values in words.items()}
        flags={base:block_flags(values)[1] for base,values in words.items()}
        result[phase]={"raw_word":words,"change_mask":masks,"flags":flags}
    return result

def audit(training_session,replication_session,train_frames,train_markers,
          test_frames,test_markers):
    if training_session==replication_session:
        raise ValueError("Independent replication requires distinct sessions")
    bases=tuple(sorted(set(x for pair in PAIRS for x in pair)))
    for base in bases:
        if not START<=base<=END-3:raise ValueError("Control block outside captured window")
    train=features(train_frames,train_markers,bases)
    test=features(test_frames,test_markers,bases)
    rows=[]
    for phase in PHASES:
        for left,right in PAIRS:
            for feature in ("change_mask","raw_word"):
                xa,ya=train[phase][feature][left],train[phase][feature][right]
                xb,yb=test[phase][feature][left],test[phase][feature][right]
                result=model(xa,ya,xb,yb,alphabet=tuple(range(16)) if feature=="change_mask" else ())
                fa,fb=train[phase]["flags"][left],train[phase]["flags"][right]
                ga,gb=test[phase]["flags"][left],test[phase]["flags"][right]
                old=compare_flags(fa,fb)
                new=compare_flags(ga,gb)
                rows.append(dict(training_session=training_session,
                    replication_session=replication_session,phase=phase,
                    left=f"0x{left:06X}",right=f"0x{right:06X}",
                    pair_type="candidate" if (left,right)==PAIRS[0] else "negative_control",
                    feature=feature,train_frames=len(xa),test_frames=len(xb),
                    baseline_accuracy=result["baseline_accuracy"],
                    conditional_accuracy=result["conditional_accuracy"],
                    accuracy_gain=result["accuracy_gain"],
                    baseline_logloss=result["baseline_logloss"],
                    conditional_logloss=result["conditional_logloss"],
                    logloss_gain=result["logloss_gain"],
                    seen_fraction=result["seen_fraction"],
                    train_sync_given_either=old[5],test_sync_given_either=new[5],
                    train_phi=old[4],test_phi=new[4],
                    note="independent_session_prediction_not_spatial_validation"))
    summaries=[]
    for left,right in PAIRS:
        relevant=[r for r in rows if r["left"]==f"0x{left:06X}" and r["right"]==f"0x{right:06X}"
                  and r["feature"]=="change_mask"]
        summaries.append(dict(training_session=training_session,
            replication_session=replication_session,
            left=f"0x{left:06X}",right=f"0x{right:06X}",
            pair_type="candidate" if (left,right)==PAIRS[0] else "negative_control",
            mean_test_accuracy_gain_mask=sum(r["accuracy_gain"] for r in relevant)/len(relevant),
            min_test_accuracy_gain_mask=min(r["accuracy_gain"] for r in relevant),
            mean_test_logloss_gain_mask=sum(r["logloss_gain"] for r in relevant)/len(relevant),
            mean_test_sync=sum(r["test_sync_given_either"] for r in relevant
                               if r["test_sync_given_either"]!="")/
                           max(1,sum(r["test_sync_given_either"]!="" for r in relevant)),
            phases=len(relevant),note="descriptive_compare_controls_no_multiple_test_correction"))
    return rows,summaries

def run(training_session,replication_session,root):
    a,ma=load(training_session,root)
    b,mb=load(replication_session,root)
    rows,summaries=audit(training_session,replication_session,a,ma,b,mb)
    out=root/"output"/"csv"
    stem=f"spatial_v3_0_{training_session}__{replication_session}"
    paths=(out/(stem+"_replication.csv"),out/(stem+"_control_summary.csv"))
    if any(p.exists() for p in paths):raise FileExistsError("Refusing overwrite of replication outputs")
    for path,fields,data in zip(paths,(FIELDS,SUMMARY),(rows,summaries)):
        with path.open("x",encoding="utf8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=fields)
            writer.writeheader();writer.writerows(data)
    return paths,(rows,summaries)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("training_session")
    p.add_argument("replication_session")
    p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    paths,groups=run(args.training_session,args.replication_session,args.root.resolve())
    for path,group in zip(paths,groups):print("Wrote",path,"rows",len(group))
    print("Experimental independent-session comparison only. No coordinate validation.")
