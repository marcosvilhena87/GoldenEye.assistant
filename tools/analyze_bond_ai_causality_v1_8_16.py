"""v1.8.16 controlled Freeze/release audit. Observation is not proof of causality."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path
B=(0x0D33EC,0x0D33F4)
A=(0x06D248,0x06D250)
PHASES=("BASELINE","CONTROL_MOVE","CONTROL_SOLDIER_RESPONSE","RESET_ORIGIN",
"AI_FREEZE_REQUEST","AI_FREEZE_CONFIRMED","DECOUPLE_MOVE","DECOUPLE_BOND_STILL",
"SOLDIER_OLD_TARGET","AI_RELEASE_REQUEST","AI_RELEASE_CONFIRMED",
"BOND_STILL_POST_RELEASE","SOLDIER_RETARGET_OBSERVED","REPEAT_RESET",
"REPEAT_AI_FREEZE","REPEAT_MOVE","REPEAT_RELEASE","REPEAT_RETARGET")
def numeric(raw):
 try:
  val=struct.unpack(">f",bytes.fromhex(raw))[0]
  return val if math.isfinite(val) and abs(val)<1e8 else None
 except (ValueError,TypeError,struct.error):return None
def analyze(sid,root=Path("output/csv")):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid SID")
 stem=Path(root)/f"bond_ai_causality_v1_8_16_{sid}"
 def load(s):
  with Path(str(stem)+s).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
 rows=load("_timeline.csv");markers=load("_markers.csv");ending=load("_termination.csv")
 if not rows:raise ValueError("empty timeline")
 data=defaultdict(dict);phase={}
 for row in rows:
  if row["session"]!=sid:raise ValueError("foreign session")
  n=int(row["frame"]);o=int(row["offset_hex"],16)
  if o in data[n]:raise ValueError("duplicate field per frame")
  if n in phase and phase[n]!=row["phase"]:raise ValueError("phase mismatch")
  phase[n]=row["phase"];data[n][o]=row["raw_be"]
 frames=sorted(data);counts=defaultdict(int);values=defaultdict(lambda:{"A":[],"B":[]})
 for n in frames:
  p=phase[n];counts[p]+=1
  for name,pair in (("A",A),("B",B)):
   xy=[numeric(data[n].get(o)) for o in pair]
   if all(x is not None for x in xy):values[p][name].append((n,xy))
 def stats(group):
  out={}
  for name,seq in group.items():
   if not seq:out[name]={"samples":0};continue
   start=seq[0][1];finish=seq[-1][1]
   out[name]={"samples":len(seq),"first":start,"last":finish,
    "net_vector":[finish[i]-start[i] for i in range(2)],
    "net_distance":math.dist(start,finish),
    "spread":[max(v[i] for _,v in seq)-min(v[i] for _,v in seq) for i in range(2)],
    "raw_value_changes":sum(v!=w for (_,v),(_,w) in zip(seq,seq[1:]))}
  if all(group[name] for name in ("A","B")):
   a,b=group["A"],group["B"];same={n:xy for n,xy in a}
   gap=[math.dist(same[n],xy) for n,xy in b if n in same]
   out["A_B_numeric_gap"]={"max":max(gap),"first":gap[0],"last":gap[-1]} if gap else None
  return out
 detail={p:stats(values[p]) for p in PHASES}
 freeze=("AI_FREEZE_CONFIRMED","DECOUPLE_MOVE","DECOUPLE_BOND_STILL","SOLDIER_OLD_TARGET")
 def same_across(phases,name):
  seq=[tuple(data[n].get(o) for o in (A if name=="A" else B))
       for n in frames if phase[n] in phases and all(o in data[n] for o in (A if name=="A" else B))]
  return bool(seq and len(set(seq))==1),len(seq)
 a_stable,a_frames=same_across(freeze,"A")
 b_stable,b_frames=same_across(("DECOUPLE_BOND_STILL","SOLDIER_OLD_TARGET"),"B")
 release=("BOND_STILL_POST_RELEASE","SOLDIER_RETARGET_OBSERVED")
 bond_after_release,bond_n=same_across(release,"B")
 return {"protocol":"bond_ai_causality_v1_8_16","session":sid,"frames":len(frames),
  "complete":bool(ending and ending[-1].get("reason")=="stop" and
                  all(b==a+1 for a,b in zip(frames,frames[1:]))),
  "phase_frame_counts":{p:counts[p] for p in PHASES},
  "phase_numeric_stats":detail,
  "freeze_phase_A_constant":a_stable,"freeze_phase_A_frames":a_frames,
  "bond_still_before_release_B_constant":b_stable,
  "bond_still_after_release_B_constant":bond_after_release,
  "bond_still_after_release_frames":bond_n,
  "markers":markers,
  "causality_validated":False,"physical_coordinates_validated":False,
  "notes":["Operator labels are claims, not measurements of active RAM Freeze or soldier intent.",
    "Distinguish first frame of release from a verified RAM value change.",
    "A frozen AI-location candidate may affect multiple game subsystems.",
    "Soldier movement and pursuing a particular point must be independently confirmed visually.",
    "Never freeze B during A-only Freeze interventions; save a state beforehand."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 report=analyze(a.session,a.root);out=a.root/f"bond_ai_causality_v1_8_16_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Bond AI causality v1.8.16",out,"frames",report["frames"],"complete",report["complete"],
  "A frozen",report["freeze_phase_A_constant"])
if __name__=="__main__":main()
