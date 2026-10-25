"""Experimental proximity convergence: compare selected Bond and Soldier words by frame."""
import argparse,csv,json,math,struct
from pathlib import Path
from collections import defaultdict
BOND=(0x0D33E8,0x0D33EC,0x0D33F0,0x0D33F4,0x06D248,0x06D250,0x06D254)
SOLDIER=(0x20F594,0x20F5AC,0x20F580,0x20F578,0x20F57C,0x06A120,0x06A124,0x06A128,0x06A154,0x06A15C,0x20F728,0x20F730)
def analyze(sid,root=Path("output/csv"),min_frames=30):
 if not sid or ".." in sid or any(x in sid for x in "/\\\r\n"):raise ValueError("unsafe SID")
 path=root/f"soldier_chase_v1_8_8_1_{sid}_timeline.csv"
 with path.open(encoding="utf-8",newline="") as f:rows=csv.DictReader(f);data=list(rows)
 frames=defaultdict(dict);phases={}
 for r in data:
  if r["session"]!=sid:raise ValueError("session mismatch")
  n=int(r["frame"]);off=int(r["offset_hex"],16)
  if off in frames[n]:raise ValueError("duplicate row")
  frames[n][off]=r["raw_be"]
  if n in phases and phases[n]!=r["phase"]:raise ValueError("mixed phase")
  phases[n]=r["phase"]
 result=[]
 for a in BOND:
  for b in SOLDIER:
   for fmt in (">f","<f"):
    samples={}
    for phase in ("BOND_APPROACH","BOND_RETREAT","SOLDIER_CHASE","BASELINE"):
     sub=[]
     for n in sorted(frames):
      if phases[n]!=phase or a not in frames[n] or b not in frames[n]:continue
      x=struct.unpack(fmt,bytes.fromhex(frames[n][a]))[0]
      y=struct.unpack(fmt,bytes.fromhex(frames[n][b]))[0]
      if math.isfinite(x) and math.isfinite(y) and abs(x)<1e8 and abs(y)<1e8:
       sub.append((n,abs(x-y)))
     if len(sub)>=min_frames:
      first,final=sub[0][1],sub[-1][1]
      samples[phase]={"frames":len(sub),"initial_abs_difference":first,"final_abs_difference":final,
       "delta_abs_difference":final-first,"minimum_abs_difference":min(v for _,v in sub)}
    approach=samples.get("BOND_APPROACH");retreat=samples.get("BOND_RETREAT")
    if not approach:continue
    converged=approach["delta_abs_difference"]<0
    diverged=bool(retreat and retreat["delta_abs_difference"]>0)
    result.append({"bond_offset":f"0x{a:06X}","soldier_offset":f"0x{b:06X}",
      "float_format":fmt,"approach_converged":converged,"retreat_diverged":diverged,
      "phase_metrics":samples,"diagnostic_only":True})
 result.sort(key=lambda r:(-int(r["approach_converged"] and r["retreat_diverged"]),-int(r["approach_converged"]),r["bond_offset"],r["soldier_offset"]))
 return {"protocol":"soldier_proximity_convergence_v1_8_8_2","session":sid,
  "pairs_evaluated":len(result),"pairs":result,
  "physical_distance_validated":False,"bond_world_coordinates_validated":False,"soldier_world_coordinates_validated":False,
  "limitations":["Absolute scalar difference cannot recover 2D/3D Euclidean distance.","Both values may be unvalidated or share duplicate state.","Approach and retreat require independent visual confirmation of physical movement.","An unrelated dynamic field can converge coincidentally.","Save persistence and XYZ assignment unvalidated."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 report=analyze(a.session,a.root)
 out=a.root/f"soldier_proximity_v1_8_8_2_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Proximity:",out,"pairs:",report["pairs_evaluated"])
if __name__=="__main__":main()
