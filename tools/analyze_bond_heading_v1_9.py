"""Rank rotation-responsive RDRAM candidates without asserting heading semantics."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path
TURN=("TURN_LEFT","TURN_RIGHT","TURN_FULL_CIRCLE","AIM_ON_NO_TARGET_TURN","AIM_OFF_NO_TARGET_TURN")
STILL=("BASELINE_STILL","STILL_LEFT","STILL_RETURN","STILL_FULL_CIRCLE","STILL_AFTER_MOVE","STILL_FINAL")
MOVE=("MOVE_FORWARD","MOVE_BACK")
WATCH=("0x0D3998","0x0D3D40","0x0D36F4","0x0D3720","0x0D33EC","0x0D33F4","0x06D248","0x06D250")
def decode(raw):
 try:
  n=struct.unpack(">f",bytes.fromhex(raw))[0]
  return n if math.isfinite(n) and abs(n)<1e7 else None
 except (TypeError,ValueError,struct.error):return None
def analyze(sid,root=Path("output/csv"),minimum_frames=30):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid sid")
 stem=Path(root)/f"bond_heading_v1_9_{sid}"
 def load(s):
  with Path(str(stem)+s).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 timeline=load("_timeline.csv");ending=load("_termination.csv");markers=load("_markers.csv")
 frames=defaultdict(dict);phase={}
 for row in timeline:
  if row["session"]!=sid:raise ValueError("foreign session")
  n=int(row["frame"]);o=row["offset_hex"].upper()
  if o in frames[n]:raise ValueError("duplicate offset")
  if n in phase and phase[n]!=row["phase"]:raise ValueError("mixed phase")
  frames[n][o]=row["raw_be"];phase[n]=row["phase"]
 if not frames:raise ValueError("empty capture")
 ordered=sorted(frames);gaps=[[a,b] for a,b in zip(ordered,ordered[1:]) if b!=a+1]
 offsets=sorted({o for record in frames.values() for o in record})
 result=[]
 for o in offsets:
  metrics={}
  for p in STILL+TURN+MOVE:
   seq=[(n,frames[n][o]) for n in ordered if phase[n]==p and o in frames[n]]
   if len(seq)<minimum_frames:
    metrics[p]={"available":False,"frames":len(seq)};continue
   vals=[x for _,x in seq];fs=[decode(x) for x in vals]
   changes=sum(a!=b for a,b in zip(vals,vals[1:]))
   numerical=all(v is not None for v in fs)
   metrics[p]={"available":True,"frames":len(seq),"raw_changes":changes,
    "distinct_raw":len(set(vals)),"first_raw":vals[0],"last_raw":vals[-1],
    "delta_float_be":fs[-1]-fs[0] if numerical else None,
    "float_spread":max(fs)-min(fs) if numerical else None}
  tv=[metrics[p] for p in TURN if metrics[p]["available"]]
  sv=[metrics[p] for p in STILL if metrics[p]["available"]]
  mv=[metrics[p] for p in MOVE if metrics[p]["available"]]
  turn_rate=sum(x["raw_changes"] for x in tv)/max(1,sum(x["frames"]-1 for x in tv))
  still_rate=sum(x["raw_changes"] for x in sv)/max(1,sum(x["frames"]-1 for x in sv))
  move_rate=sum(x["raw_changes"] for x in mv)/max(1,sum(x["frames"]-1 for x in mv))
  scored=bool(tv and sv and mv)
  result.append({"offset":o,"tracked":o in WATCH,"phases":metrics,
    "turn_change_rate":turn_rate,"still_change_rate":still_rate,
    "move_change_rate":move_rate,
    "rotation_specificity_score":max(0,turn_rate-still_rate-move_rate) if scored else None,
    "has_required_controls":scored,
    "status":"candidate_not_validated_heading"})
 result.sort(key=lambda r:(-1 if r["rotation_specificity_score"] is None else -r["rotation_specificity_score"],r["offset"]))
 return {"protocol":"bond_heading_discovery_v1_9","session":sid,"frames":len(ordered),
   "complete":bool(ending and ending[-1].get("reason")=="stop" and not gaps),
   "gaps":gaps,"markers":markers,"candidates":result,
   "heading_validated":False,"angle_scale_validated":False,
   "notes":["Rank is change-rate discrimination, not a measurement of angle.",
            "Unaligned u8 leads are recorded as four-byte windows; inspect the relevant byte.",
            "Frame rate, camera movement, translation during turning and auto-aim must be controlled.",
            "No independent rotation-angle, yaw wrap-around or ROM/core identity verified."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 r=analyze(a.session,a.root);dest=a.root/f"bond_heading_v1_9_{a.session}_analysis.json"
 if dest.exists():raise FileExistsError(dest)
 dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Bond heading v1.9",dest,"frames",r["frames"],"complete",r["complete"])
if __name__=="__main__":main()
