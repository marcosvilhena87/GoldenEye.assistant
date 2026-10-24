"""v2.5: offline temporal checks for v2.4 candidates; never validates coordinates."""
import argparse,csv,math,statistics
from pathlib import Path
try:
    from .analyze_spatial_position_v2_4 import load,decode,PHASES,END
except ImportError:
    from analyze_spatial_position_v2_4 import load,decode,PHASES,END

ADDRESSES=(0x3B30D0,0x3B30E0,0x3B30EC)
KINDS={2:("be_i16","be_u16"),4:("be_f32","le_f32","be_i32","be_u32")}
HOLDS=("P0_HOLD","P1_HOLD","P0_RETURN_HOLD","P0_ROTATED_HOLD","P2_HOLD")
PHASE_COLS=("session","address","width","interpretation","phase","frames","finite_fraction",
"median","mad","unique","change_rate","first","last","net_delta","total_variation","max_jump","jump_fraction")
CHECK_COLS=("session","address","width","interpretation","p0","p1","return_p0","rotated_p0","p2",
"step1","step_back","step2","return_error","rotation_shift","holds_stable","return_close",
"rotation_stable","first_reverse","second_shift","evidence_for","evidence_against","status")

def summary(values,session,address,width,kind,phase):
 finite=all(math.isfinite(v) for v in values)
 diffs=[b-a for a,b in zip(values,values[1:])] if finite else []
 nums=[v for v in values if math.isfinite(v)]
 mid=statistics.median(nums) if nums else None
 mad=statistics.median(abs(v-mid) for v in nums) if nums else None
 nz=sorted(abs(v) for v in diffs if v!=0)
 baseline=statistics.median(nz) if nz else 0
 return dict(session=session,address=f"0x{address:06X}",width=width,interpretation=kind,
 phase=phase,frames=len(values),finite_fraction=len(nums)/len(values),
 median=mid,mad=mad,unique=len(set(values)),change_rate=sum(v!=0 for v in diffs)/max(1,len(diffs)),
 first=values[0],last=values[-1],net_delta=values[-1]-values[0] if finite else "",
 total_variation=sum(abs(v) for v in diffs) if finite else "",
 max_jump=max((abs(v) for v in diffs),default=0) if finite else "",
 jump_fraction=sum(v>10*baseline for v in nz)/len(nz) if baseline and nz else 0)

def audit(session,frames,markers,tail=120):
 if tail<10:raise ValueError("tail must be >=10")
 phase_frames={p:range(markers[i],markers[i+1]) for i,p in enumerate(PHASES)}
 summaries=[];checks=[]
 for address in ADDRESSES:
  for width,kinds in KINDS.items():
   if address+width-1>END:continue
   for kind in kinds:
    series={p:[decode(bytes(frames[f][address+j] for j in range(width)),kind) for f in fs]
            for p,fs in phase_frames.items()}
    summaries.extend(summary(series[p],session,address,width,kind,p) for p in PHASES)
    if any(len(series[p])<tail for p in HOLDS):raise ValueError("Insufficient HOLD frames")
    hold=[summary(series[p][-tail:],session,address,width,kind,p) for p in HOLDS]
    finite=all(row["finite_fraction"]==1 for row in hold)
    med=[row["median"] for row in hold]
    a,b,c,d,e=med
    step1=b-a if finite else None
    back=c-b if finite else None
    step2=e-d if finite else None
    scale=max(abs(step1),abs(back),abs(step2),1e-9) if finite else None
    ret=abs(c-a) if finite else None
    rot=abs(d-c) if finite else None
    stable=finite and max(row["mad"] for row in hold)<=.02*scale
    ret_ok=finite and ret<=.1*scale
    rot_ok=finite and rot<=.1*scale
    reverse=finite and step1*back<0
    second=finite and abs(step2)>.01*scale
    yes=[];no=[]
    if not finite:no.append("nonfinite_hold_values")
    if reverse:yes.append("first_displacement_reversed")
    else:no.append("no_opposite_return")
    if ret_ok:yes.append("returned_to_initial")
    else:no.append("return_not_close")
    if rot_ok:yes.append("rotation_invariant")
    else:no.append("rotation_shift")
    if stable:yes.append("holds_low_mad")
    else:no.append("hold_variability")
    if second:yes.append("second_forward_shift")
    else:no.append("no_second_forward_shift_in_this_field")
    if finite and any(abs(v)>1e30 for v in med):no.append("extreme_magnitude")
    for p in ("FORWARD","BACK","FORWARD_AGAIN"):
     activity=summary(series[p],session,address,width,kind,p)
     if activity["change_rate"]==0:no.append("no_temporal_changes_"+p)
    # Only a follow-up independent experiment can confirm a coordinate.
    state="experimental_support" if not no else "inconclusive_or_contradicted"
    checks.append(dict(session=session,address=f"0x{address:06X}",width=width,
      interpretation=kind,p0=a,p1=b,return_p0=c,rotated_p0=d,p2=e,
      step1=step1,step_back=back,step2=step2,return_error=ret,rotation_shift=rot,
      holds_stable=stable,return_close=ret_ok,rotation_stable=rot_ok,
      first_reverse=reverse,second_shift=second,evidence_for=";".join(yes),
      evidence_against=";".join(no),status=state))
 return summaries,checks

def run(session,root,tail=120):
 frames,markers=load(session,root)
 summaries,checks=audit(session,frames,markers,tail)
 base=root/"output/csv"/("spatial_v2_5_"+session)
 paths=[Path(str(base)+"_phase_summary.csv"),Path(str(base)+"_candidate_checks.csv")]
 if any(p.exists() for p in paths):raise FileExistsError("Refusing overwrite")
 for path,fields,rows in zip(paths,(PHASE_COLS,CHECK_COLS),(summaries,checks)):
  with path.open("x",newline="",encoding="utf8") as fh:
   writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader();writer.writerows(rows)
 return paths,(summaries,checks)

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("session")
 p.add_argument("--root",type=Path,default=Path("."));p.add_argument("--tail",type=int,default=120)
 a=p.parse_args()
 paths,groups=run(a.session,a.root.resolve(),a.tail)
 for path,rows in zip(paths,groups):print("Wrote",path,"rows",len(rows))
 print("Experimental classifications only; no canonical mapping updates.")
