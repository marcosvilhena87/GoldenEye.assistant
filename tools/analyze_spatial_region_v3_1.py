"""Spatial v3.1: regional, cross-session dependency discovery.

Offline read-only analysis of the complete 80-byte window captured by v2.4.
No inferred physical coordinates or canonical mapping updates.
"""
import argparse
import csv
import math
from collections import Counter
from itertools import combinations
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES, START, END
    from .analyze_spatial_shared_source_v2_8 import block_flags, compare_flags
    from .analyze_spatial_dependency_v2_9 import model
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES, START, END
    from analyze_spatial_shared_source_v2_8 import block_flags, compare_flags
    from analyze_spatial_dependency_v2_9 import model

BLOCKS=tuple(range(START,END+1,4))
PAIRS=tuple(combinations(BLOCKS,2))
DETAIL_COLS=("original","replica","phase","left","right","train_events",
             "test_events","train_phi","test_phi","train_sync","test_sync",
             "seen_fraction","baseline_accuracy","conditional_accuracy",
             "accuracy_gain","logloss_gain","mask_agreement","status")
PAIR_COLS=("original","replica","left","right","phases","mean_accuracy_gain",
           "min_accuracy_gain","mean_logloss_gain","mean_test_sync",
           "mean_test_phi","positive_gain_phases","supported_phases",
           "interpretation")
GROUP_COLS=("original","replica","block","component","component_size",
            "members","edges","rule")

def get_phases(frames,bounds):
    answer={}
    for i,phase in enumerate(PHASES):
        ids=range(bounds[i],bounds[i+1])
        n=len(ids)
        if n<12:raise ValueError("Phase too short: "+phase)
        words={base:[tuple(frames[f][base+j] for j in range(4)) for f in ids]
               for base in BLOCKS}
        answer[phase]={base:block_flags(words[base]) for base in BLOCKS}
    return answer

def audit(original,replica,first,bounds1,second,bounds2,
          threshold_gain=.02,threshold_sync=.9,min_phases=7):
    if original==replica:raise ValueError("Replication must be a distinct session")
    if not 0<=threshold_sync<=1 or not -1<=threshold_gain<=1:
        raise ValueError("Invalid thresholds")
    if not 1<=min_phases<=len(PHASES):raise ValueError("Invalid min_phases")
    a,b=get_phases(first,bounds1),get_phases(second,bounds2)
    details=[];summaries=[]
    for left,right in PAIRS:
        aggregate=[]
        for phase in PHASES:
            am,ac=a[phase][left];bm,bc=a[phase][right]
            cm,cc=b[phase][left];dm,dc=b[phase][right]
            prediction=model(am,bm,cm,dm,alphabet=tuple(range(16)))
            train=compare_flags(ac,bc);test=compare_flags(cc,dc)
            agreement=sum(x==y for x,y in zip(cm,dm))/len(cm)
            good=(prediction["accuracy_gain"]>=threshold_gain
                  and test[5]!="" and test[5]>=threshold_sync)
            row=dict(original=original,replica=replica,phase=phase,
                left=f"0x{left:06X}",right=f"0x{right:06X}",
                train_events=len(am),test_events=len(cm),
                train_phi=train[4],test_phi=test[4],
                train_sync=train[5],test_sync=test[5],
                seen_fraction=prediction["seen_fraction"],
                baseline_accuracy=prediction["baseline_accuracy"],
                conditional_accuracy=prediction["conditional_accuracy"],
                accuracy_gain=prediction["accuracy_gain"],
                logloss_gain=prediction["logloss_gain"],
                mask_agreement=agreement,
                status="candidate_relation" if good else "insufficient_evidence")
            details.append(row);aggregate.append(row)
        def mean(key):
            nums=[float(row[key]) for row in aggregate if row[key]!=""]
            return sum(nums)/len(nums) if nums else ""
        ok=sum(r["status"]=="candidate_relation" for r in aggregate)
        summaries.append(dict(original=original,replica=replica,
            left=f"0x{left:06X}",right=f"0x{right:06X}",
            phases=len(aggregate),mean_accuracy_gain=mean("accuracy_gain"),
            min_accuracy_gain=min(r["accuracy_gain"] for r in aggregate),
            mean_logloss_gain=mean("logloss_gain"),
            mean_test_sync=mean("test_sync"),mean_test_phi=mean("test_phi"),
            positive_gain_phases=sum(r["accuracy_gain"]>0 for r in aggregate),
            supported_phases=ok,
            interpretation="replicated_pair_candidate" if ok>=min_phases
                           else "unconfirmed"))
    # Connected components are descriptive, not established structures.
    parent={x:x for x in BLOCKS}
    def root(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def union(x,y):
        x,y=root(x),root(y)
        if x!=y:parent[max(x,y)]=min(x,y)
    edges=[]
    for r in summaries:
        if r["interpretation"]=="replicated_pair_candidate":
            x,y=int(r["left"],16),int(r["right"],16)
            edges.append((x,y));union(x,y)
    connected={}
    for x in BLOCKS:connected.setdefault(root(x),[]).append(x)
    counts=Counter(root(x) for x,y in edges)
    groups=[]
    for idx,(component,members) in enumerate(sorted(connected.items()),1):
        names=";".join(f"0x{x:06X}" for x in members)
        for x in members:
            groups.append(dict(original=original,replica=replica,
                block=f"0x{x:06X}",component=idx,component_size=len(members),
                members=names,edges=counts.get(component,0),
                rule=f"gain>={threshold_gain};sync>={threshold_sync};phases>={min_phases}"))
    return details,summaries,groups

OUTPUTS=(("_phase_pairs.csv",DETAIL_COLS),
         ("_pair_summary.csv",PAIR_COLS),
         ("_components.csv",GROUP_COLS))
def run(original,replica,root,threshold_gain=.02,threshold_sync=.9,min_phases=7):
    f1,m1=load(original,root);f2,m2=load(replica,root)
    results=audit(original,replica,f1,m1,f2,m2,
                  threshold_gain,threshold_sync,min_phases)
    dest=root/"output"/"csv"
    stem=f"spatial_v3_1_{original}__{replica}"
    paths=[dest/(stem+s) for s,_ in OUTPUTS]
    if any(p.exists() for p in paths):raise FileExistsError("Refusing to overwrite v3.1 results")
    for path,(_,fields),rows in zip(paths,OUTPUTS,results):
        with path.open("x",encoding="utf8",newline="") as fh:
            writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader()
            writer.writerows(rows)
    return paths,results

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("original");p.add_argument("replica")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--threshold-gain",type=float,default=.02)
    p.add_argument("--threshold-sync",type=float,default=.9)
    p.add_argument("--min-phases",type=int,default=7)
    args=p.parse_args()
    paths,groups=run(args.original,args.replica,args.root.resolve(),
                     args.threshold_gain,args.threshold_sync,args.min_phases)
    for path,rows in zip(paths,groups):print(f"Wrote {path} rows={len(rows)}")
    print("Exploratory regional pairs only: no coordinate or structure validation.")
