"""Spatial v2.8: offline shared-source evidence from validated v2.4 samples.

Co-updates, value mappings, and joint transitions are observations, not proof
of a shared pointer, common owner, engine cycle, or physical coordinates.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES
    from .analyze_spatial_structure_v2_6 import BASES, phi
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES
    from analyze_spatial_structure_v2_6 import BASES, phi

PAIRS=tuple(combinations(BASES,2))
BLOCK_FIELDS=("session","phase","left","right","frames","both_changed",
              "only_left","only_right","neither","phi","sync_given_either",
              "byte_mask_equal_fraction","both_all_four_changed",
              "shared_changed_byte_fraction","null_trials",
              "null_phi_max","empirical_one_sided_p")
VALUE_FIELDS=("session","phase","left","right","frames","distinct_left",
              "distinct_right","distinct_pairs","forward_determinism",
              "reverse_determinism","modal_pair_fraction","top_pairs",
              "pair_collision_fraction","note")
EVENT_FIELDS=("session","phase","left","right","joint_events",
              "unique_joint_transitions","top_joint_transitions",
              "simultaneous_fraction","left_change_fraction","right_change_fraction")

def mask(words,i):
    return sum(1<<j for j in range(4) if words[i][j]!=words[i-1][j])

def block_flags(words):
    masks=[mask(words,i) for i in range(1,len(words))]
    return masks,[int(m!=0) for m in masks]

def compare_flags(a,b):
    both=sum(x and y for x,y in zip(a,b))
    left=sum(x and not y for x,y in zip(a,b))
    right=sum(y and not x for x,y in zip(a,b))
    neither=len(a)-both-left-right
    return (both,left,right,neither,phi(both,left,right,neither),
            both/(both+left+right) if both+left+right else "")

def shifts(n,cap):
    # Exclude near-zero shifts, deterministically sample more distant shifts.
    choices=[s for s in range(1,n) if min(s,n-s)>3]
    if len(choices)<=cap:return choices
    if cap==1:return [choices[len(choices)//2]]
    return [choices[i*(len(choices)-1)//(cap-1)] for i in range(cap)]

def null_control(a,b,trials):
    obs=compare_flags(a,b)[4]
    samples=[]
    for shift in shifts(len(b),trials):
        other=b[-shift:]+b[:-shift]
        val=compare_flags(a,other)[4]
        if val!="":samples.append(val)
    return (len(samples),max(samples) if samples else "",
            (1+sum(x>=obs for x in samples))/(len(samples)+1)
            if obs!="" and samples else "")

def determinism(xs,ys):
    # Weighted dominant mapping confidence P(mode(Y|X)), over observed X.
    mapping=defaultdict(Counter)
    for x,y in zip(xs,ys):mapping[x][y]+=1
    return sum(max(counts.values()) for counts in mapping.values())/len(xs)

def audit(session,frames,boundaries,null_trials=199):
    if null_trials<3:raise ValueError("null_trials must be >=3")
    blocks,values,events=[],[],[]
    for i,phase in enumerate(PHASES):
        frame_ids=range(boundaries[i],boundaries[i+1])
        words={base:[tuple(frames[f][base+j] for j in range(4))
                      for f in frame_ids] for base in BASES}
        n=len(words[BASES[0]])
        if n<8:raise ValueError("Phase too short: "+phase)
        flags={base:block_flags(seq) for base,seq in words.items()}
        for left,right in PAIRS:
            a=words[left];b=words[right]
            am,ac=flags[left];bm,bc=flags[right]
            both,l_only,r_only,neither,co_phi,sync=compare_flags(ac,bc)
            trials,max_null,p=null_control(ac,bc,null_trials)
            equal_masks=sum(x==y for x,y in zip(am,bm))/len(am)
            overlap=sum((x&y).bit_count() for x,y in zip(am,bm))
            union=sum((x|y).bit_count() for x,y in zip(am,bm))
            blocks.append(dict(session=session,phase=phase,left=f"0x{left:06X}",
                right=f"0x{right:06X}",frames=len(am),both_changed=both,
                only_left=l_only,only_right=r_only,neither=neither,
                phi=co_phi,sync_given_either=sync,
                byte_mask_equal_fraction=equal_masks,
                both_all_four_changed=sum(x==15 and y==15 for x,y in zip(am,bm)),
                shared_changed_byte_fraction=overlap/union if union else "",
                null_trials=trials,null_phi_max=max_null,empirical_one_sided_p=p))
            count=Counter(zip(a,b))
            values.append(dict(session=session,phase=phase,left=f"0x{left:06X}",
                right=f"0x{right:06X}",frames=n,distinct_left=len(set(a)),
                distinct_right=len(set(b)),distinct_pairs=len(count),
                forward_determinism=determinism(a,b),
                reverse_determinism=determinism(b,a),
                modal_pair_fraction=count.most_common(1)[0][1]/n,
                top_pairs=";".join("{}>{}:{}".format(
                    bytes(x).hex().upper(),bytes(y).hex().upper(),c)
                    for (x,y),c in count.most_common(5)),
                pair_collision_fraction=1-len(count)/n,
                note="in_sample_mapping_can_overfit_unique_values"))
            transitions=Counter()
            for k in range(1,n):
                if ac[k-1] and bc[k-1]:
                    transitions[(a[k-1],a[k],b[k-1],b[k])]+=1
            events.append(dict(session=session,phase=phase,left=f"0x{left:06X}",
                right=f"0x{right:06X}",joint_events=both,
                unique_joint_transitions=len(transitions),
                top_joint_transitions=";".join("{}>{}|{}>{}:{}".format(
                    bytes(x).hex().upper(),bytes(y).hex().upper(),
                    bytes(z).hex().upper(),bytes(t).hex().upper(),c)
                    for (x,y,z,t),c in transitions.most_common(5)),
                simultaneous_fraction=both/len(ac),
                left_change_fraction=sum(ac)/len(ac),
                right_change_fraction=sum(bc)/len(bc)))
    return blocks,values,events

OUTPUTS=(
 ("_block_sync.csv",BLOCK_FIELDS),
 ("_value_dependency.csv",VALUE_FIELDS),
 ("_joint_events.csv",EVENT_FIELDS),
)

def run(session,root,null_trials=199):
    frames,boundaries=load(session,root)
    results=audit(session,frames,boundaries,null_trials)
    paths=[root/"output"/"csv"/("spatial_v2_8_"+session+suffix)
           for suffix,_ in OUTPUTS]
    if any(path.exists() for path in paths):
        raise FileExistsError("Refusing to overwrite v2.8 output")
    for path,(_,fields),rows in zip(paths,OUTPUTS,results):
        with path.open("x",encoding="utf8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return paths,results

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--null-trials",type=int,default=199)
    a=parser.parse_args()
    paths,results=run(a.session,a.root.resolve(),a.null_trials)
    for path,rows in zip(paths,results):
        print(f"Wrote {path} rows={len(rows)}")
    print("Read-only experimental evidence; no coordinates or shared source validated.")
