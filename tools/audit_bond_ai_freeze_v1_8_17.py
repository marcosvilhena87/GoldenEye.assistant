"""v1.8.17: offline freeze integrity and visual annotation correlation audit."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path
A=(0x06D248,0x06D250); B=(0x0D33EC,0x0D33F4)
FROZEN=("AI_FREEZE_CONFIRMED","DECOUPLE_MOVE","DECOUPLE_BOND_STILL","SOLDIER_OLD_TARGET")
REPEAT=("REPEAT_AI_FREEZE","REPEAT_MOVE")
RELEASE=("AI_RELEASE_REQUEST","AI_RELEASE_CONFIRMED","BOND_STILL_POST_RELEASE","SOLDIER_RETARGET_OBSERVED")
def vec(raw):
 try:
  result=[struct.unpack(">f",bytes.fromhex(x))[0] for x in raw]
  return result if all(math.isfinite(v) and abs(v)<1e8 for v in result) else None
 except (TypeError,ValueError,struct.error):return None
def audit(sid,root=Path("output/csv"),observations=None):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid sid")
 base=Path(root)/f"bond_ai_causality_v1_8_16_{sid}"
 raw=defaultdict(dict);phase={}
 with Path(str(base)+"_timeline.csv").open(newline="",encoding="utf-8") as f:
  for row in csv.DictReader(f):
   if row["session"]!=sid:raise ValueError("mixed session")
   n=int(row["frame"]);o=int(row["offset_hex"],16)
   if o in raw[n]:raise ValueError("duplicate field")
   if n in phase and phase[n]!=row["phase"]:raise ValueError("phase inconsistency")
   raw[n][o]=row["raw_be"];phase[n]=row["phase"]
 if not raw:raise ValueError("empty capture")
 frames=sorted(raw);phase_events=defaultdict(list)
 events=[]
 prev=None
 for n in frames:
  if not all(o in raw[n] for o in A+B):continue
  a=tuple(raw[n][o] for o in A);b=tuple(raw[n][o] for o in B)
  va=vec(a);vb=vec(b)
  dist=math.dist(va,vb) if va is not None and vb is not None else None
  record={"frame":n,"phase":phase[n],"a":a,"b":b,"distance":dist}
  phase_events[phase[n]].append(record)
  if prev and n==prev["frame"]+1 and (a!=prev["a"] or b!=prev["b"]):
   events.append({"frame":n,"phase":phase[n],"a_changed":a!=prev["a"],
                  "b_changed":b!=prev["b"],"a_b_gap":dist,
                  "a_vector":va,"b_vector":vb})
  prev=record
 by_phase={}
 for p,items in phase_events.items():
  by_phase[p]={"frames":len(items),"a_unique_raw":len({r["a"] for r in items}),
    "b_unique_raw":len({r["b"] for r in items}),
    "a_changed_within_phase":sum(x["a_changed"] for x in events if x["phase"]==p and x["frame"]>items[0]["frame"]),
    "b_changed_within_phase":sum(x["b_changed"] for x in events if x["phase"]==p and x["frame"]>items[0]["frame"]),
    "gap_first":items[0]["distance"],"gap_last":items[-1]["distance"],
    "gap_max":max((r["distance"] for r in items if r["distance"] is not None),default=None)}
 def stable(phases,offsets):
  values=[tuple(raw[n].get(o) for o in offsets) for n in frames
          if phase[n] in phases and all(o in raw[n] for o in offsets)]
  changes=sum(a!=b for a,b in zip(values,values[1:]))
  return {"frames":len(values),"distinct_raw":len(set(values)), "transitions":changes,
          "constant":bool(values and len(set(values))==1)}
 treatments={"first_freeze":stable(FROZEN,A),
             "repeat_freeze":stable(REPEAT,A),
             "bond_stationary_after_release":stable(("BOND_STILL_POST_RELEASE","SOLDIER_RETARGET_OBSERVED"),B)}
 # Measure numerical events on the timeline without assuming that the annotation
 # frame is when a user toggled Freeze or that an AI target changed.
 def first_match(start_phases,comparison):
  return next((e for e in events if e["phase"] in start_phases and comparison(e)),None)
 release_a=first_match(RELEASE,lambda e:e["a_changed"] and not e["b_changed"])
 observed=[]
 if observations is not None:
  with Path(observations).open(newline="",encoding="utf-8") as f:
   reader=csv.DictReader(f)
   expected={"session","frame","event","confidence","notes"}
   if not expected.issubset(reader.fieldnames or []):raise ValueError("observation header missing columns")
   for row in reader:
    if row["session"]!=sid:raise ValueError("foreign observation")
    n=int(row["frame"])
    if n not in raw:raise ValueError("observation frame outside capture")
    if row["event"] not in {"SOLDIER_OLD_TARGET_VISUAL","SOLDIER_RETARGET_VISUAL","NO_RETARGET_VISUAL","UNCERTAIN"}:
     raise ValueError("invalid visual observation")
    observed.append({"frame":n,"phase":phase[n],"event":row["event"],
                     "confidence":row["confidence"],"notes":row["notes"],
                     "frames_from_first_release_numeric_event":n-release_a["frame"] if release_a else None})
 return {"protocol":"bond_ai_freeze_integrity_behavior_v1_8_17",
   "session":sid,"frames":len(frames),
   "phase_integrity":by_phase,"treatments":treatments,
   "first_release_a_only_change":release_a,
   "a_only_updates":[e for e in events if e["a_changed"] and not e["b_changed"]],
   "b_only_updates":[e for e in events if e["b_changed"] and not e["a_changed"]],
   "observations":observed,"visual_evidence_available":bool(observed),
   "freeze_proven_continuous":False,"soldier_target_causality_proven":False,
   "limitations":["The RAM collector samples once per frame, not on every internal write.",
     "Phase annotations cannot confirm the actual Freeze toggle frame.",
     "An observation CSV represents operator annotation and not measured soldier coordinates.",
     "Cross-phase A constancy matters more than individual per-phase motion counts.",
     "Correlated visual behavior does not exclude other game state changes."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--observations",type=Path);a=p.parse_args()
 r=audit(a.session,a.root,a.observations)
 path=a.root/f"bond_ai_v1_8_17_{a.session}_analysis.json"
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Bond–AI v1.8.17",path,"frames",r["frames"],"freeze A distinct",
       r["treatments"]["first_freeze"]["distinct_raw"])
if __name__=="__main__":main()
