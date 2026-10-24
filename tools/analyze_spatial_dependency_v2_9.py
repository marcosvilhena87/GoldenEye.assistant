"""Spatial v2.9: chronological out-of-sample dependency audit of v2.4 capture.

No assumed addresses, no emulator mutation, no coordinate validation.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES
    from .analyze_spatial_structure_v2_6 import BASES
    from .analyze_spatial_shared_source_v2_8 import block_flags
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES
    from analyze_spatial_structure_v2_6 import BASES
    from analyze_spatial_shared_source_v2_8 import block_flags

PAIRS=tuple(combinations(BASES,2))
EVAL_FIELDS=("session","train_phase","test_phase","left","right","direction",
             "feature","train_n","test_n","seen_fraction","baseline_accuracy",
             "conditional_accuracy","accuracy_gain","baseline_logloss",
             "conditional_logloss","logloss_gain","baseline_brier",
             "conditional_brier","brier_gain","note")
TRANS_FIELDS=("session","phase","left","right","left_mask","right_mask",
              "count","conditional_fraction","phase_events")

def representations(frames,boundaries):
    phases={}
    for i,phase in enumerate(PHASES):
        ids=range(boundaries[i],boundaries[i+1])
        words={base:[tuple(frames[f][base+j] for j in range(4)) for f in ids]
               for base in BASES}
        n=len(words[BASES[0]])
        if n<12:raise ValueError("Phase too short: "+phase)
        masks={base:block_flags(seq)[0] for base,seq in words.items()}
        phases[phase]={"raw_word":words,"change_mask":masks}
    return phases

def model(train_x,train_y,test_x,test_y,alphabet=(),smoothing=1):
    if not train_x or not test_x or len(train_x)!=len(train_y) or len(test_x)!=len(test_y):
        raise ValueError("Empty or misaligned evaluation")
    # The vocabulary is frozen from training. A reserved UNSEEN class permits
    # finite and fair scoring of unseen test values for both models.
    vocab=set(train_y)|set(alphabet)
    unseen=object()
    vocab.add(unseen)
    k=len(vocab)
    counts=Counter(train_y)
    joint=defaultdict(Counter)
    for x,y in zip(train_x,train_y):joint[x][y]+=1
    majority=counts.most_common(1)[0][0]
    by_x={x:c.most_common(1)[0][0] for x,c in joint.items()}
    base_ok=cond_ok=seen=0
    base_loss=cond_loss=base_brier=cond_brier=0.0
    total=len(train_y)
    for x,y in zip(test_x,test_y):
        target=y if y in vocab else unseen
        base_ok+=y==majority
        if x in joint:
            seen+=1
            local=joint[x]
            local_n=sum(local.values())
            predicted=by_x[x]
            # Probability estimates shrink to global predictive distribution.
            base_p=(counts.get(target,0)+smoothing)/(total+smoothing*k)
            cond_p=(local.get(target,0)+smoothing*base_p)/(local_n+smoothing)
        else:
            predicted=majority
            base_p=(counts.get(target,0)+smoothing)/(total+smoothing*k)
            cond_p=base_p
        cond_ok+=y==predicted
        base_loss-=math.log(base_p)
        cond_loss-=math.log(cond_p)
        # Binary event-vs-not proxy, not a multiclass Brier score.
        base_brier+=(1-base_p)**2
        cond_brier+=(1-cond_p)**2
    n=len(test_x)
    return dict(train_n=len(train_x),test_n=n,seen_fraction=seen/n,
                baseline_accuracy=base_ok/n,conditional_accuracy=cond_ok/n,
                accuracy_gain=(cond_ok-base_ok)/n,
                baseline_logloss=base_loss/n,conditional_logloss=cond_loss/n,
                logloss_gain=(base_loss-cond_loss)/n,
                baseline_brier=base_brier/n,conditional_brier=cond_brier/n,
                brier_gain=(base_brier-cond_brier)/n)

def audit(session,frames,boundaries,split=0.7):
    if not .2<=split<=.8:raise ValueError("split must be between 0.2 and 0.8")
    phases=representations(frames,boundaries)
    evaluations,transitions=[],[]
    for phase in PHASES:
        for left,right in PAIRS:
            a=phases[phase]["change_mask"][left]
            b=phases[phase]["change_mask"][right]
            counts=Counter(zip(a,b))
            left_count=Counter(a)
            for (x,y),n in sorted(counts.items()):
                transitions.append(dict(session=session,phase=phase,
                    left=f"0x{left:06X}",right=f"0x{right:06X}",
                    left_mask=x,right_mask=y,count=n,
                    conditional_fraction=n/left_count[x],phase_events=len(a)))
    for feature in ("raw_word","change_mask"):
        for left,right in PAIRS:
            for direction,source,target in (("forward",left,right),("reverse",right,left)):
                for i,phase in enumerate(PHASES):
                    data=phases[phase][feature]
                    xs,ys=data[source],data[target]
                    cut=int(len(xs)*split)
                    # No event can cross the split: change masks are already
                    # formed wholly within this experimental phase.
                    experiments=[(phase,phase,xs[:cut],ys[:cut],xs[cut:],ys[cut:])]
                    if i==0:
                        for later in PHASES[1:]:
                            other=phases[later][feature]
                            experiments.append((phase,later,xs,ys,other[source],other[target]))
                    for train_phase,test_phase,train_x,train_y,test_x,test_y in experiments:
                        metrics=model(train_x,train_y,test_x,test_y,
                            alphabet=tuple(range(16)) if feature=="change_mask" else ())
                        evaluations.append(dict(session=session,train_phase=train_phase,
                            test_phase=test_phase,left=f"0x{source:06X}",
                            right=f"0x{target:06X}",direction=direction,feature=feature,
                            **metrics,note="chronological_holdout" if train_phase==test_phase
                            else "train_P0_hold_test_other_phase"))
    return evaluations,transitions

OUTPUTS=(
 ("_out_of_sample.csv",EVAL_FIELDS),
 ("_conditional_transitions.csv",TRANS_FIELDS),
)
def run(session,root,split=.7):
    frames,boundaries=load(session,root)
    outputs=audit(session,frames,boundaries,split)
    paths=[root/"output"/"csv"/("spatial_v2_9_"+session+suffix) for suffix,_ in OUTPUTS]
    if any(p.exists() for p in paths):raise FileExistsError("Refusing to overwrite v2.9 output")
    for path,(_,fields),rows in zip(paths,OUTPUTS,outputs):
        with path.open("x",newline="",encoding="utf8") as fp:
            writer=csv.DictWriter(fp,fieldnames=fields)
            writer.writeheader();writer.writerows(rows)
    return paths,outputs

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("session");p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--split",type=float,default=.7)
    args=p.parse_args()
    paths,groups=run(args.session,args.root.resolve(),args.split)
    for path,rows in zip(paths,groups):print(f"Wrote {path} rows={len(rows)}")
    print("Exploratory dependence, not physical or causal validation.")
