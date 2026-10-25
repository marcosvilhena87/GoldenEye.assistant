"""Bond Heading v1.9.7 — camera/body/weapon-aim separation audit."""
import argparse,csv,json,re,math
from collections import defaultdict
from pathlib import Path
TURN=("C_LEFT","C_RIGHT")
VERTICAL=("C_UP","C_DOWN")
RETICLE=("R_STICK_LEFT","R_STICK_RIGHT","R_STICK_UP","R_STICK_DOWN")
CONTROLS=("BASELINE_STILL","WEAPON_CHANGE","MOVE_FORWARD_NO_TURN")
AUX=("aux_0D3998","aux_0D3D40","aux_0D39A0","aux_0D3D48")
def principal(v):return (v+180)%360-180
def audit(sid,root=Path("output/csv")):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid SID")
 stem=root/f"bond_heading_hud_v1_9_7_{sid}"
 def load(s):
  with Path(str(stem)+s).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
 rows=load("_samples.csv");events=load("_events.csv");term=load("_termination.csv")
 if not rows:raise ValueError("empty samples")
 if any(x["session"]!=sid for x in rows+events+term):raise ValueError("mixed session")
 frames=[int(r["frame"]) for r in rows]
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 groups=[];current=None
 for r in rows:
  if current is None or current["phase"]!=r["phase"]:
   current={"phase":r["phase"],"samples":[]};groups.append(current)
  current["samples"].append(r)
 segments=[]
 for index,g in enumerate(groups):
  samples=g["samples"];valid=[r for r in samples if r["valid"]=="1"]
  def num(r,k):
   try:return float(r[k]) if r.get(k) not in ("",None) else None
   except ValueError:return None
  angles=[num(r,"angle_deg") for r in valid if num(r,"angle_deg") is not None]
  steps=[num(r,"step_deg") for r in valid if num(r,"step_deg") is not None]
  a={k:sum(x[k]!=y[k] for x,y in zip(samples,samples[1:])) for k in AUX}
  segments.append({"index":index,"phase":g["phase"],"start_frame":int(samples[0]["frame"]),
   "end_frame":int(samples[-1]["frame"]),"frames":len(samples),"valid_frames":len(valid),
   "first_angle_deg":angles[0] if angles else None,"last_angle_deg":angles[-1] if angles else None,
   "net_modulo_deg":principal(angles[-1]-angles[0]) if angles else None,
   "cumulative_steps_deg":sum(steps),"positive_steps":sum(v>0 for v in steps),
   "negative_steps":sum(v<0 for v in steps),"aux_changes":a,
   "max_norm_error":max((abs(num(r,"norm_squared")-1) for r in valid if num(r,"norm_squared") is not None),default=None),
   "resets":sum(bool(r.get("reset_reason")) for r in samples)})
 ack=[e for e in events if e["event"]!="STOP"]
 seq=[int(e["seq"]) for e in ack]
 complete=(bool(term and term[-1]["reason"]=="stop" and events and events[-1]["event"]=="STOP")
           and not gaps and len(set(frames))==len(frames) and seq==list(range(1,len(seq)+1)))
 measures=[{"phase":g["phase"],"index":g["index"],"abs_cumulative_deg":abs(g["cumulative_steps_deg"]),
   "aux_changes":sum(g["aux_changes"].values())} for g in segments if g["phase"] in TURN+VERTICAL+RETICLE+CONTROLS+("AUTOAIM_TARGET",)]
 return {"version":"v1.9.7","sid":sid,"complete":complete,"frames":len(rows),
  "valid_frames":sum(r["valid"]=="1" for r in rows),"gaps":gaps,
  "ack_count":len(ack),"segments":segments,"control_comparison":measures,
  "physical_bond_heading_validated":False,"weapon_aim_offsets_validated":False,
  "caveats":["Operator phase labels do not prove controller action occurred.",
    "R+analog may move reticle rather than camera; confirm visually.",
    "Raw auxiliary changes establish only correlation, not aim-coordinate semantics.",
    "Without independent body/camera observables, the test cannot conclusively separate body from camera."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("sid");p.add_argument("--root",type=Path,default=Path("output/csv"))
 a=p.parse_args();r=audit(a.sid,a.root)
 dest=a.root/f"bond_heading_hud_v1_9_7_{a.sid}_audit.json"
 if dest.exists():raise FileExistsError(dest)
 dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Bond heading v1.9.7",dest,"frames",r["frames"],"complete",r["complete"])
if __name__=="__main__":main()
