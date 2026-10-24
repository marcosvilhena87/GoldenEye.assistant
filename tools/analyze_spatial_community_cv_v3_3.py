"""Spatial v3.3: temporal cross-validation and shift-null controls.

Read-only. Candidate pairs are preselected from v3.2; inferential results
remain exploratory because both sessions informed candidate selection.
"""
import argparse
import csv
import math
from collections import Counter
from pathlib import Path

try:
    from .analyze_spatial_position_v2_4 import load,PHASES
    from .analyze_spatial_region_v3_1 import get_phases,BLOCKS
    from .analyze_spatial_dependency_v2_9 import model
    from .analyze_spatial_shared_source_v2_8 import shifts
except ImportError:
    from analyze_spatial_position_v2_4 import load,PHASES
    from analyze_spatial_region_v3_1 import get_phases,BLOCKS
    from analyze_spatial_dependency_v2_9 import model
    from analyze_spatial_shared_source_v2_8 import shifts

PHASE_FIELDS=("original","replica","phase","left","right","community","train_n",
              "test_n","test_segment","accuracy_gain","logloss_gain","seen_fraction",
              "null_trials","null_gain_median","null_gain_max","empirical_p_accuracy",
              "null_logloss_median","empirical_p_logloss","note")
GROUP_FIELDS=("original","replica","community","test_segment","pairs","evaluations",
              "mean_gain","median_gain","mean_logloss_gain","fraction_positive",
              "fraction_p_le_005_unadjusted","note")
NULL_FIELDS=("original","replica","phase","left","right","test_segment",
             "shift","null_accuracy_gain","null_logloss_gain")
PAIR_FIELDS=("original","replica","left","right","community","evaluations",
             "mean_gain","min_gain","mean_logloss_gain","fraction_positive",
             "min_empirical_p_accuracy","note")

def median(data):
    xs=sorted(data)
    if not xs:return ""
    n=len(xs)
    return xs[n//2] if n%2 else (xs[n//2-1]+xs[n//2])/2

def empirical_p(observed,null):
    return (1+sum(v>=observed for v in null))/(len(null)+1) if null else ""

def candidate_edges(rows):
    chosen={}
    for r in rows:
        if r["direct"] not in ("1","True","true"):continue
        x,y=int(r["left"],16),int(r["right"],16)
        if not x<y or x not in BLOCKS or y not in BLOCKS:raise ValueError("Invalid edge")
        chosen[(x,y)]=r
    return chosen

def communities(rows):
    mapping={}
    for r in rows:
        addr=int(r["block"],16)
        if addr not in BLOCKS or addr in mapping:raise ValueError("Invalid community")
        mapping[addr]=(r["component"],r["community"])
    if set(mapping)!=set(BLOCKS):raise ValueError("Incomplete community list")
    return mapping

def audit(original,replica,first,bounds1,second,bounds2,edges,community_rows,
          trials=19,split=.5):
    if original==replica:raise ValueError("Distinct sessions required")
    if not 3<=trials<=199:raise ValueError("null_trials must be in [3,199]")
    if not .25<=split<=.75:raise ValueError("split must be [0.25,0.75]")
    chosen=candidate_edges(edges)
    belongs=communities(community_rows)
    if not chosen:raise ValueError("No selected edges")
    a,b=get_phases(first,bounds1),get_phases(second,bounds2)
    phase_rows=[];null_rows=[]
    for left,right in sorted(chosen):
        l=f"0x{left:06X}";r=f"0x{right:06X}"
        ca=belongs[left];cb=belongs[right]
        community=f"{ca[0]}:{ca[1]}" if ca==cb else "cross_community"
        for phase in PHASES:
            train_x=a[phase][left][0];train_y=a[phase][right][0]
            test_x=b[phase][left][0];test_y=b[phase][right][0]
            if len(test_x)<24:raise ValueError("Phase too short for temporal split")
            cut=int(len(test_x)*split)
            for segment,x,y in (("early",test_x[:cut],test_y[:cut]),
                                ("late",test_x[cut:],test_y[cut:])):
                if len(x)<8:raise ValueError("Insufficient split data")
                observed=model(train_x,train_y,x,y,alphabet=tuple(range(16)))
                # Rotate target independently within the same test segment.
                # Keep frozen training model/baseline and marginal frequencies.
                # Disallow near-zero rotations; cannot remove all autocorrelation.
                controls=[]
                for shift in shifts(len(y),trials):
                    shifted=y[-shift:]+y[:-shift]
                    metric=model(train_x,train_y,x,shifted,alphabet=tuple(range(16)))
                    controls.append(metric)
                    null_rows.append(dict(original=original,replica=replica,
                        phase=phase,left=l,right=r,test_segment=segment,shift=shift,
                        null_accuracy_gain=metric["accuracy_gain"],
                        null_logloss_gain=metric["logloss_gain"]))
                accuracy_null=[m["accuracy_gain"] for m in controls]
                loss_null=[m["logloss_gain"] for m in controls]
                phase_rows.append(dict(original=original,replica=replica,
                    phase=phase,left=l,right=r,community=community,
                    train_n=len(train_x),test_n=len(x),test_segment=segment,
                    accuracy_gain=observed["accuracy_gain"],
                    logloss_gain=observed["logloss_gain"],
                    seen_fraction=observed["seen_fraction"],
                    null_trials=len(controls),null_gain_median=median(accuracy_null),
                    null_gain_max=max(accuracy_null) if accuracy_null else "",
                    empirical_p_accuracy=empirical_p(observed["accuracy_gain"],accuracy_null),
                    null_logloss_median=median(loss_null),
                    empirical_p_logloss=empirical_p(observed["logloss_gain"],loss_null),
                    note="post_selection_exploratory_p_not_adjusted"))
    def summarize(records,fields):
        gains=[float(x["accuracy_gain"]) for x in records]
        losses=[float(x["logloss_gain"]) for x in records]
        output=dict(evaluations=len(records),mean_gain=sum(gains)/len(gains),
            mean_logloss_gain=sum(losses)/len(losses),
            fraction_positive=sum(x>0 for x in gains)/len(gains))
        return output
    groups=[]
    for community in sorted(set(r["community"] for r in phase_rows)):
        for segment in ("early","late"):
            sub=[r for r in phase_rows if r["community"]==community and r["test_segment"]==segment]
            if not sub:continue
            metrics=summarize(sub,None)
            groups.append(dict(original=original,replica=replica,community=community,
                test_segment=segment,pairs=len({(r["left"],r["right"]) for r in sub}),
                **metrics,median_gain=median([r["accuracy_gain"] for r in sub]),
                fraction_p_le_005_unadjusted=sum(r["empirical_p_accuracy"]!="" and
                    float(r["empirical_p_accuracy"])<=.05 for r in sub)/len(sub),
                note="same_sessions_preselected_pairs_no_multiplicity_control"))
    pairs=[]
    for left,right in sorted(chosen):
        sub=[r for r in phase_rows if r["left"]==f"0x{left:06X}" and r["right"]==f"0x{right:06X}"]
        metric=summarize(sub,None)
        pairs.append(dict(original=original,replica=replica,left=sub[0]["left"],
            right=sub[0]["right"],community=sub[0]["community"],
            **metric,min_gain=min(float(r["accuracy_gain"]) for r in sub),
            min_empirical_p_accuracy=min(float(r["empirical_p_accuracy"]) for r in sub
                if r["empirical_p_accuracy"]!=""),
            note="descriptive_min_p_not_significant"))
    return phase_rows,groups,null_rows,pairs

OUTPUTS=(("_phase_holdouts.csv",PHASE_FIELDS),("_community_summary.csv",GROUP_FIELDS),
         ("_shift_null.csv",NULL_FIELDS),("_pair_summary.csv",PAIR_FIELDS))
def read_csv(path):
    with path.open(encoding="utf8",newline="") as fh:return list(csv.DictReader(fh))

def run(original,replica,root,trials=19,split=.5):
    folder=root/"output"/"csv"
    stem=f"spatial_v3_2_{original}__{replica}"
    edges=read_csv(folder/(stem+"_edges.csv"))
    memberships=read_csv(folder/(stem+"_communities.csv"))
    if len(edges)!=190 or len(memberships)!=20:raise ValueError("Incomplete v3.2 input")
    if any(r["original"]!=original or r["replica"]!=replica for r in edges+memberships):
        raise ValueError("v3.2 source/session mismatch")
    first,b1=load(original,root);second,b2=load(replica,root)
    output=audit(original,replica,first,b1,second,b2,edges,memberships,trials,split)
    prefix=folder/f"spatial_v3_3_{original}__{replica}"
    paths=[Path(str(prefix)+suffix) for suffix,_ in OUTPUTS]
    if any(p.exists() for p in paths):raise FileExistsError("Refusing to overwrite v3.3 results")
    for path,(_,fields),records in zip(paths,OUTPUTS,output):
        with path.open("x",encoding="utf8",newline="") as fh:
            w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(records)
    return paths,output

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("original");p.add_argument("replica")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--null-trials",type=int,default=19)
    p.add_argument("--split",type=float,default=.5)
    args=p.parse_args()
    paths,records=run(args.original,args.replica,args.root.resolve(),
                      trials=args.null_trials,split=args.split)
    for path,data in zip(paths,records):print(f"Wrote {path} rows={len(data)}")
    print("Exploratory cross-validation only; no independently held-out discovery session.")
