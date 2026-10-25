"""v1.8.10 offline same-frame distance and frozen-field integrity audit."""
import argparse,csv,json,math,struct
from pathlib import Path
from collections import defaultdict,Counter
CONFIGS={
 "historical":((0x06D248,0x06D250),(0x20F594,0x20F5AC)),
 "alternate":((0x06D248,0x06D250),(0x20F578,0x20F580)),
 "duplicate_region":((0x06D248,0x06D250),(0x06A120,0x06A128)),
 "alias":((0x0D33EC,0x0D33F4),(0x20F594,0x20F5AC)),
}
STAGES=("FROZEN_BASELINE","BOND_APPROACH","BOND_STOP_NEAR","BOND_ROTATE","BOND_RETREAT","BOND_STOP_FAR")
def read(path):
 with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def val(s):
 try:
  x=struct.unpack(">f",bytes.fromhex(s))[0]
  return x if math.isfinite(x) and abs(x)<1e8 else None
 except (ValueError,struct.error):return None
def analyze(sid,root=Path("output/csv"),minimum_frames=30):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid SID")
 if minimum_frames<2:raise ValueError("minimum frames invalid")
 stem=root/("soldier_frozen_v1_8_10_"+sid)
 rows=read(Path(str(stem)+"_timeline.csv"));marks=read(Path(str(stem)+"_markers.csv"));end=read(Path(str(stem)+"_termination.csv"))
 if not rows:raise ValueError("empty timeline")
 frames=defaultdict(dict);phase={}
 for r in rows:
  if r["session"]!=sid:raise ValueError("mixed SID")
  n=int(r["frame"]);o=int(r["offset_hex"],16)
  if o in frames[n]:raise ValueError("duplicate field")
  frames[n][o]=r["raw_be"]
  if n in phase and phase[n]!=r["phase"]:raise ValueError("inconsistent phase")
  phase[n]=r["phase"]
 numbers=sorted(frames);gaps=[[a,b] for a,b in zip(numbers,numbers[1:]) if b!=a+1]
 results=[]
 for name,(bond,soldier) in CONFIGS.items():
  data=defaultdict(list);raws=defaultdict(list);invalid=0
  for n in numbers:
   addresses=(*bond,*soldier)
   if any(o not in frames[n] for o in addresses):invalid+=1;continue
   decoded=[val(frames[n][o]) for o in addresses]
   if any(x is None for x in decoded):invalid+=1;continue
   ba,bb,sa,sb=decoded
   data[phase[n]].append((n,math.hypot(sa-ba,sb-bb)))
   raws[phase[n]].append((n,frames[n][soldier[0]],frames[n][soldier[1]]))
  stats={}
  for stage in STAGES:
   samples=data[stage]
   if len(samples)<minimum_frames:
    stats[stage]={"available":False,"frames":len(samples)}
    continue
   minimum=min(samples,key=lambda p:p[1])
   raw=raws[stage]
   changes=sum(raw[i][1:]!=raw[i-1][1:] for i in range(1,len(raw)))
   stats[stage]={"available":True,"frames":len(samples),"start_distance":samples[0][1],
                 "end_distance":samples[-1][1],"minimum_distance":minimum[1],"minimum_frame":minimum[0],
                 "distance_spread":max(v for _,v in samples)-min(v for _,v in samples),
                 "soldier_raw_changes":changes,"soldier_constant":changes==0}
  frozen_stages=[stats[s] for s in STAGES if stats[s]["available"]]
  fully_stable=bool(frozen_stages and all(s["soldier_constant"] for s in frozen_stages))
  # Also verify stability *across* all stages, rather than only within stages.
  frozen_frames=[(n,frames[n][soldier[0]],frames[n][soldier[1]]) for n in numbers
                 if phase[n] in STAGES and soldier[0] in frames[n] and soldier[1] in frames[n]]
  overall_constant=bool(frozen_frames and len({(a,b) for _,a,b in frozen_frames})==1)
  a=stats["BOND_APPROACH"];r=stats["BOND_RETREAT"];rot=stats["BOND_ROTATE"]
  convergence=bool(a["available"] and a["end_distance"]<a["start_distance"])
  divergence=bool(r["available"] and r["end_distance"]>r["start_distance"])
  rotation_quiet=bool(rot["available"] and rot["distance_spread"]<=0.01)
  results.append({"config":name,"bond_offsets":[f"0x{o:06X}" for o in bond],
   "soldier_offsets":[f"0x{o:06X}" for o in soldier],"stages":stats,
   "frozen_fields_constant_across_stages":overall_constant,
   "frozen_fields_constant_within_each_stage":fully_stable,
   "approach_converged":convergence,"retreat_diverged":divergence,
   "rotation_distance_stable":rotation_quiet,
   "controlled_convergence_supported":bool(overall_constant and convergence and divergence and rotation_quiet),
   "invalid_frames":invalid})
 return {"protocol":"soldier_frozen_bond_motion_v1_8_10","session":sid,"frames":len(numbers),
  "capture_complete":bool(end and end[-1].get("reason")=="stop" and not gaps),"gaps":gaps,
  "markers":marks,"results":results,"physical_distance_validated":False,
  "identity_validated":False,"axes_validated":False,"save_persistence_validated":False,
  "limitations":["Freeze is operator-controlled, not independently validated via game cheat state.",
                 "Frozen-field stability is a necessary check, but not sufficient to identify the soldier.",
                 "Bond references and candidate axes are experimental float32 big-endian.",
                 "Rotating Bond should not change actual distance, but transient effects and camera fields may change.",
                 "Same-frame bytes were read sequentially and are not an atomic RAM snapshot."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 report=analyze(a.session,a.root);out=a.root/f"soldier_frozen_v1_8_10_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Soldier frozen v1.8.10",out,"frames",report["frames"],"complete",report["capture_complete"])
if __name__=="__main__":main()
