"""v1.8.13 Bond position candidate validation, read-only offline analysis."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path
BOND=((0x06D248,0x06D250),(0x0D33EC,0x0D33F4))
SOLDIER=((0x20F594,0x20F5AC),(0x20F578,0x20F580),(0x06A120,0x06A128))
STILL=("ORIGIN_STILL","ORIGIN_AFTER_ROTATION","DESTINATION_STILL","RETURN_STILL","DESTINATION_REPEAT_STILL","RETURN_REPEAT_STILL")
MOVING=("ROTATE_LEFT","ROTATE_RIGHT","MOVE_FORWARD","MOVE_BACK","MOVE_FORWARD_REPEAT","MOVE_BACK_REPEAT")
PHASES=STILL+MOVING
def decode(raw):
 try:
  n=struct.unpack(">f",bytes.fromhex(raw))[0]
  return n if math.isfinite(n) and abs(n)<1e8 else None
 except (TypeError,ValueError,struct.error):return None
def analyze(sid,root=Path("output/csv"),minimum_frames=30):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid SID")
 if minimum_frames<2:raise ValueError("minimum_frames")
 stem=Path(root)/f"bond_position_v1_8_13_{sid}"
 def read(s):
  with Path(str(stem)+s).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 timeline=read("_timeline.csv");marks=read("_markers.csv");end=read("_termination.csv")
 if not timeline:raise ValueError("empty timeline")
 frames=defaultdict(dict);phase={}
 for r in timeline:
  if r["session"]!=sid:raise ValueError("mixed session")
  frame=int(r["frame"]);off=int(r["offset_hex"],16)
  if off in frames[frame]:raise ValueError("duplicate frame/offset")
  frames[frame][off]=r["raw_be"]
  if frame in phase and phase[frame]!=r["phase"]:raise ValueError("mixed phase")
  phase[frame]=r["phase"]
 ordered=sorted(frames)
 gaps=[[a,b] for a,b in zip(ordered,ordered[1:]) if b!=a+1]
 groups=defaultdict(list)
 for frame in ordered:groups[phase[frame]].append(frame)
 results=[]
 for index,bond in enumerate(BOND):
  stages={};all_soldier={}
  for label in PHASES:
   samples=[]
   for frame in groups[label]:
    xy=[decode(frames[frame].get(off)) for off in bond]
    if any(x is None for x in xy):continue
    samples.append((frame,*xy))
   if len(samples)<minimum_frames:
    stages[label]={"available":False,"frames":len(samples)};continue
   first=samples[0];last=samples[-1]
   distances=[math.hypot(samples[i][1]-samples[i-1][1],samples[i][2]-samples[i-1][2]) for i in range(1,len(samples))]
   spreads=[max(s[j] for s in samples)-min(s[j] for s in samples) for j in (1,2)]
   stages[label]={"available":True,"frames":len(samples),
     "first":[first[1],first[2]],"last":[last[1],last[2]],
     "net_distance":math.hypot(last[1]-first[1],last[2]-first[2]),
     "path_length":sum(distances),"spread_components":spreads,
     "first_frame":first[0],"last_frame":last[0]}
  origin=stages["ORIGIN_STILL"];returns={}
  for label in ("ORIGIN_AFTER_ROTATION","RETURN_STILL","RETURN_REPEAT_STILL"):
   item=stages[label]
   returns[label]=(math.hypot(origin["first"][0]-item["first"][0],origin["first"][1]-item["first"][1])
     if origin["available"] and item["available"] else None)
  destinations=stages["DESTINATION_STILL"];repeated=stages["DESTINATION_REPEAT_STILL"]
  destination_error=(math.hypot(destinations["first"][0]-repeated["first"][0],
                                  destinations["first"][1]-repeated["first"][1])
                     if destinations["available"] and repeated["available"] else None)
  all_stills=[stages[s] for s in STILL if stages[s]["available"]]
  max_still_spread=max((math.hypot(*s["spread_components"]) for s in all_stills),default=None)
  checks=[]
  for soldier in SOLDIER:
   values=[]
   for n in ordered:
    if phase[n] not in PHASES:continue
    if all(o in frames[n] for o in soldier):values.append(tuple(frames[n][o] for o in soldier))
   checks.append({"offsets":[f"0x{o:06X}" for o in soldier],"frames":len(values),
                   "constant_across_phases":bool(values and len(set(values))==1)})
  results.append({"bond_pair":[f"0x{o:06X}" for o in bond],"pair_index":index,
   "stages":stages,"return_error_by_phase":returns,"repeat_destination_error":destination_error,
   "max_still_numeric_spread":max_still_spread,"soldier_candidates":checks,
   "position_validation_status":"candidate_not_validated"})
 aliases=[]
 for a,b in ((0x06D248,0x0D33EC),(0x06D250,0x0D33F4)):
  valid=[n for n in ordered if a in frames[n] and b in frames[n]]
  aliases.append({"left":f"0x{a:06X}","right":f"0x{b:06X}",
    "frames_compared":len(valid),"raw_equal_fraction":sum(frames[n][a]==frames[n][b] for n in valid)/len(valid) if valid else None})
 return {"protocol":"bond_position_candidate_validation_v1_8_13","session":sid,"frames":len(ordered),
  "capture_complete":bool(end and end[-1].get("reason")=="stop" and not gaps),
  "gaps":gaps,"phase_frame_counts":{s:len(groups[s]) for s in PHASES},"markers":marks,
  "results":results,"aliases":aliases,"physical_xyz_validated":False,
  "cross_save_validated":False,
  "limitations":["Return-to-origin errors are numeric and depend on operator returning to the same physical point.",
    "A rotation can include small displacements, and these scripts do not record controller inputs.",
    "Stationary controls and frozen-soldier raw constancy do not prove world-coordinate semantics.",
    "Cross-save matching requires separate captures; offsets are not automatically persistent."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 report=analyze(a.session,a.root)
 out=a.root/f"bond_position_v1_8_13_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Bond position v1.8.13",out,"frames",report["frames"],"complete",report["capture_complete"])
if __name__=="__main__":main()
