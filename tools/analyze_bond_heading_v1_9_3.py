"""Bond Heading v1.9.3 — angular reconstruction from experimental unit vector."""
import argparse,csv,json,math,re,struct
from collections import defaultdict
from pathlib import Path
X=0x0D33F8;Y=0x0D3400
HOLDS=("BASELINE_STILL","HOLD_90","HOLD_180","HOLD_270","HOLD_360","HOLD_R270","HOLD_R180","HOLD_R90","HOLD_ORIGIN","HOLD_MOVE")
TURNS=("TURN_LEFT_90","TURN_LEFT_180","TURN_LEFT_270","TURN_LEFT_360","TURN_RIGHT_270","TURN_RIGHT_180","TURN_RIGHT_90","TURN_RIGHT_0")
def f32(h):
 try:
  v=struct.unpack(">f",bytes.fromhex(h))[0]
  return v if math.isfinite(v) else None
 except (ValueError,TypeError,struct.error):return None
def principal(a):
 return (a+180.0)%360.0-180.0
def reconstruct(sid,root=Path("output/csv"),norm_tolerance=0.02):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid SID")
 prefix=root/f"bond_heading_v1_9_2_{sid}"
 def load(ext):
  with Path(str(prefix)+ext).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
 frames=defaultdict(dict);phases={}
 for r in load("_timeline.csv"):
  if r["session"]!=sid:raise ValueError("mixed session")
  n=int(r["frame"]);addr=int(r["offset_hex"],16)
  if addr in frames[n]:raise ValueError("duplicate offset")
  if n in phases and phases[n]!=r["phase"]:raise ValueError("phase conflict")
  frames[n][addr]=r["raw_be"];phases[n]=r["phase"]
 if not frames:raise ValueError("empty recording")
 term=load("_termination.csv");ordered=sorted(frames)
 gaps=[[a,b] for a,b in zip(ordered,ordered[1:]) if b!=a+1]
 timeline=[];previous=None;unwrapped=None
 for n in ordered:
  x=f32(frames[n].get(X));y=f32(frames[n].get(Y))
  if x is None or y is None:continue
  norm=x*x+y*y
  angle=math.degrees(math.atan2(y,x))
  valid=abs(norm-1)<=norm_tolerance
  step=None
  if previous is not None and n==previous["frame"]+1 and valid and previous["valid"]:
   step=principal(angle-previous["angle_deg"])
   unwrapped=previous["unwrapped_deg"]+step
  elif valid:
   unwrapped=angle
  else:unwrapped=None
  item={"frame":n,"phase":phases[n],"x":x,"y":y,"norm_squared":norm,
        "valid":valid,"angle_deg":angle,"unwrapped_deg":unwrapped,"step_deg":step}
  timeline.append(item);previous=item
 byphase={}
 for phase in dict.fromkeys(x["phase"] for x in timeline):
  samples=[x for x in timeline if x["phase"]==phase]
  good=[x for x in samples if x["valid"]]
  changes=[x["step_deg"] for x in good if x["step_deg"] is not None and x["phase"]==phase]
  byphase[phase]={"frames":len(samples),"valid":len(good),
    "first_angle_deg":good[0]["angle_deg"] if good else None,
    "last_angle_deg":good[-1]["angle_deg"] if good else None,
    "net_shortest_deg":principal(good[-1]["angle_deg"]-good[0]["angle_deg"]) if good else None,
    "integrated_turn_deg":sum(changes),
    "positive_steps":sum(x>0 for x in changes),"negative_steps":sum(x<0 for x in changes),
    "largest_step_deg":max((abs(x) for x in changes),default=0),
    "max_norm_error":max((abs(x["norm_squared"]-1) for x in samples),default=None)}
 checkpoint=[]
 for phase in HOLDS:
  if phase in byphase and byphase[phase]["valid"]:
   v=[x for x in timeline if x["phase"]==phase and x["valid"]][-1]
   checkpoint.append({"phase":phase,"frame":v["frame"],"angle_deg":v["angle_deg"],
       "relative_to_initial_deg":None,"x":v["x"],"y":v["y"]})
 if checkpoint:
  initial=checkpoint[0]["angle_deg"]
  for p in checkpoint:p["relative_to_initial_deg"]=principal(p["angle_deg"]-initial)
 # Checkpoint deviation compared with *nominal* turn labels; never physical validation.
 targets={"HOLD_90":90,"HOLD_180":180,"HOLD_270":270,"HOLD_360":0,
          "HOLD_R270":270,"HOLD_R180":180,"HOLD_R90":90,"HOLD_ORIGIN":0}
 nominal=[{"phase":p["phase"],"nominal_deg":targets[p["phase"]],
           "observed_relative_deg":p["relative_to_initial_deg"],
           "absolute_error_if_positive_convention":abs(principal(p["relative_to_initial_deg"]-targets[p["phase"]])),
           "absolute_error_if_negative_convention":abs(principal(p["relative_to_initial_deg"]+targets[p["phase"]]))}
           for p in checkpoint if p["phase"] in targets]
 report={"protocol":"bond_heading_v1_9_3","session":sid,"frames":len(ordered),
  "complete":bool(term and term[-1].get("reason")=="stop" and not gaps),
  "gaps":gaps,"vector_x":"0x0D33F8","vector_y":"0x0D3400","norm_tolerance":norm_tolerance,
  "phase_stats":byphase,"checkpoints":checkpoint,"nominal_comparisons":nominal,
  "heading_physically_calibrated":False,"orientation_convention_validated":False,
  "notes":["atan2(y,x) is a mathematical candidate, not verified game-world heading.",
           "Unwrap assumes per-frame turns are less than 180 degrees; inspect large jumps.",
           "Nominal 90/180/270 degrees are operator estimates; do not use to prove units.",
           "Only valid norm samples contribute to integrated angle."]}
 return report,timeline
def main():
 p=argparse.ArgumentParser();p.add_argument("session")
 p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--norm-tolerance",type=float,default=0.02)
 a=p.parse_args()
 if not (0<a.norm_tolerance<=0.5):p.error("invalid norm tolerance")
 report,frames=reconstruct(a.session,a.root,a.norm_tolerance)
 prefix=a.root/f"bond_heading_v1_9_3_{a.session}"
 dest=Path(str(prefix)+"_analysis.json");timeline=Path(str(prefix)+"_angles.csv")
 if dest.exists() or timeline.exists():raise FileExistsError("analysis output already exists")
 dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 fields=("frame","phase","x","y","norm_squared","valid","angle_deg","unwrapped_deg","step_deg")
 with timeline.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(frames)
 print("Heading angular v1.9.3",dest,"frames",report["frames"],"complete",report["complete"])
if __name__=="__main__":main()
