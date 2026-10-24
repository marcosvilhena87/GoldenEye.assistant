"""v2.7 offline update-cycle audit. Descriptive, no automatic coordinate validation."""
import argparse
import csv
import math
from itertools import combinations
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load, PHASES
    from .analyze_spatial_structure_v2_6 import BASES, phi
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES
    from analyze_spatial_structure_v2_6 import BASES, phi

ADDRESSES=tuple(base+i for base in BASES for i in range(4))
LAGS=(-3,-2,-1,0,1,2,3)
CYCLE_LAGS=(5,6,7,12,13,14,18,19,20)
SYNC_FIELDS=("session","phase","left","right","lag","pairs","phi","agreement",
             "both_changed","either_changed","sync_given_either","null_trials",
             "null_phi_mean","null_phi_max","empirical_one_sided_p")
PERIOD_FIELDS=("session","phase","address","lag","pairs","raw_match_rate",
               "adjacent_lag_mean","local_excess","note")
GROUP_FIELDS=("session","phase","left","right","pairs","phi","sync_given_either",
              "grouping_note")

def change_flags(xs):
    return [int(xs[i]!=xs[i-1]) for i in range(1,len(xs))]

def aligned(left,right,lag):
    # Positive lag: right occurs AFTER left. Negative: right occurs before left.
    if lag>0:return left[:-lag],right[lag:]
    if lag<0:return left[-lag:],right[:lag]
    return left,right

def compare(left,right):
    a=sum(x and y for x,y in zip(left,right))
    b=sum(x and not y for x,y in zip(left,right))
    c=sum(not x and y for x,y in zip(left,right))
    d=len(left)-a-b-c
    return dict(phi=phi(a,b,c,d),agreement=(a+d)/len(left),
                both_changed=a,either_changed=a+b+c,
                sync_given_either=a/(a+b+c) if a+b+c else "")

def circular_null(left,right,lag,cap=199):
    n=len(right)
    # Reject shifts too close to the observed lag (including wraparound).
    allowable=[s for s in range(1,n) if min(s,n-s)>max(abs(k) for k in LAGS)]
    if len(allowable)>cap:
        positions=[(i*(len(allowable)-1))//(cap-1) for i in range(cap)]
        shifts=[allowable[i] for i in positions]
    else:shifts=allowable
    values=[]
    for shift in shifts:
        rotated=right[-shift:]+right[:-shift]
        x,y=aligned(left,rotated,lag)
        val=compare(x,y)["phi"]
        if val!="":values.append(val)
    return values

def audit(session,frames,boundaries,null_trials=199):
    if null_trials<3:raise ValueError("null_trials must be >= 3")
    sync,period,groups=[],[],[]
    for index,phase in enumerate(PHASES):
        f=list(range(boundaries[index],boundaries[index+1]))
        if len(f)<24:raise ValueError("Phase too short: "+phase)
        arrays={addr:[frames[frame][addr] for frame in f] for addr in ADDRESSES}
        flags={addr:change_flags(values) for addr,values in arrays.items()}
        for left,right in combinations(ADDRESSES,2):
            a,b=flags[left],flags[right]
            for lag in (LAGS if (left%4==right%4) else (0,)):
                x,y=aligned(a,b,lag)
                obs=compare(x,y)
                null=circular_null(a,b,lag,null_trials) if (left%4==right%4) else []
                obs_phi=obs["phi"]
                p=(1+sum(value>=obs_phi for value in null))/(len(null)+1) if obs_phi!="" and null else ""
                sync.append(dict(session=session,phase=phase,left=f"0x{left:06X}",
                  right=f"0x{right:06X}",lag=lag,pairs=len(x),**obs,
                  null_trials=len(null),null_phi_mean=sum(null)/len(null) if null else "",
                  null_phi_max=max(null) if null else "",
                  empirical_one_sided_p=p))
                if lag==0:
                    groups.append(dict(session=session,phase=phase,left=f"0x{left:06X}",
                      right=f"0x{right:06X}",pairs=len(x),phi=obs_phi,
                      sync_given_either=obs["sync_given_either"],
                      grouping_note="strong_cochange_candidate" if obs_phi!="" and obs_phi>=.7 else "not_grouped"))
        for addr,values in arrays.items():
            for lag in (6,13,19):
                if lag>=len(values)-1:continue
                observed=sum(values[i]==values[i-lag] for i in range(lag,len(values)))/(len(values)-lag)
                neigh=[]
                for other in (lag-1,lag+1):
                    neigh.append(sum(values[i]==values[i-other] for i in range(other,len(values)))/(len(values)-other))
                ref=sum(neigh)/len(neigh)
                period.append(dict(session=session,phase=phase,address=f"0x{addr:06X}",
                  lag=lag,pairs=len(values)-lag,raw_match_rate=observed,
                  adjacent_lag_mean=ref,local_excess=observed-ref,
                  note="descriptive_local_lag_comparison_not_significance_test"))
    return sync,period,groups

FILES=(
 ("_leadlag.csv",SYNC_FIELDS),
 ("_cycle_lags.csv",PERIOD_FIELDS),
 ("_cochange_groups.csv",GROUP_FIELDS),
)
def run(session,root,null_trials=199):
    frames,boundaries=load(session,root)
    outputs=audit(session,frames,boundaries,null_trials)
    paths=[root/"output"/"csv"/("spatial_v2_7_"+session+suffix) for suffix,_ in FILES]
    if any(path.exists() for path in paths):raise FileExistsError("Refusing to overwrite v2.7 results")
    for path,(_,fields),rows in zip(paths,FILES,outputs):
        with path.open("x",newline="",encoding="utf8") as fh:
            writer=csv.DictWriter(fh,fieldnames=fields)
            writer.writeheader();writer.writerows(rows)
    return paths,outputs

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("session");parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--null-trials",type=int,default=199)
    args=parser.parse_args()
    paths,groups=run(args.session,args.root.resolve(),args.null_trials)
    for path,rows in zip(paths,groups):print(f"Wrote {path} rows={len(rows)}")
    print("No evidence of coordinates is automatically validated.")
