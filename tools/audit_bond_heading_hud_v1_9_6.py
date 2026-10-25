"""Read-only Bond Heading v1.9.6 physical-control and cross-session audit."""
import argparse,csv,json,math,re,statistics
from collections import defaultdict
from pathlib import Path
CONTROL=("BASELINE_STILL","HOLD_AFTER_TURN","HOLD_AFTER_MOVE","HOLD_AFTER_AIM","HOLD_AFTER_WEAPON","HOLD_AFTER_CAMERA","HOLD_LANDMARK")
ACTIVE=("BODY_TURN_LEFT","BODY_TURN_RIGHT","MOVE_FORWARD_NO_TURN","AIM_ONLY","WEAPON_CHANGE","CAMERA_ONLY","LANDMARK_MATCH")
def principal(x):return (x+180)%360-180
def audit(sid,root=Path("output/csv")):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid sid")
 p=root/f"bond_heading_hud_v1_9_6_{sid}"
 def read(s):
  with Path(str(p)+s).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 samples=read("_samples.csv");events=read("_events.csv");ending=read("_termination.csv")
 if not samples:raise ValueError("empty samples")
 if any(r["session"]!=sid for r in samples+events+ending):raise ValueError("mixed SID")
 frames=[int(r["frame"]) for r in samples]
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 def num(r,k):
  try:return float(r[k]) if r.get(k) not in ("",None) else None
  except ValueError:return None
 phases=defaultdict(list)
 for r in samples:phases[r["phase"]].append(r)
 summary={}
 for phase,rows in phases.items():
  good=[r for r in rows if r["valid"]=="1" and num(r,"angle_deg") is not None]
  steps=[num(r,"step_deg") for r in good if num(r,"step_deg") is not None]
  angles=[num(r,"angle_deg") for r in good]
  errors=[abs(num(r,"norm_squared")-1) for r in good if num(r,"norm_squared") is not None]
  # Last minus first cumulative can be misleading across REFERENCE resets.
  resets=sum(bool(r.get("reset_reason")) for r in rows)
  summary[phase]={"frames":len(rows),"valid_frames":len(good),
   "start_frame":int(rows[0]["frame"]),"end_frame":int(rows[-1]["frame"]),
   "first_angle_deg":angles[0] if angles else None,"last_angle_deg":angles[-1] if angles else None,
   "net_modulo_deg":principal(angles[-1]-angles[0]) if angles else None,
   "sum_steps_deg":sum(steps),"positive_steps":sum(x>0 for x in steps),"negative_steps":sum(x<0 for x in steps),
   "max_step_deg":max((abs(x) for x in steps),default=0),
   "max_norm_error":max(errors,default=None),"reset_count":resets}
 # Compare holds after interventions to baseline; not a physical orientation measurement.
 baseline=summary.get("BASELINE_STILL")
 pairs=[]
 if baseline and baseline["last_angle_deg"] is not None:
  for phase in CONTROL:
   if phase in summary and summary[phase]["last_angle_deg"] is not None:
    pairs.append({"phase":phase,"difference_vs_baseline_deg":principal(summary[phase]["last_angle_deg"]-baseline["last_angle_deg"])})
 acks=[e for e in events if e["event"]!="STOP"]
 ackseq=[int(x["seq"]) for x in acks]
 terminal=bool(ending and ending[-1]["reason"]=="stop" and events and events[-1]["event"]=="STOP")
 return {"version":"v1.9.6","sid":sid,"samples":len(samples),"valid_frames":sum(r["valid"]=="1" for r in samples),
  "gaps":gaps,"duplicate_frames":len(frames)!=len(set(frames)),
  "ack_sequence_ok":ackseq==list(range(1,len(ackseq)+1)),
  "stopped":terminal,"complete":terminal and not gaps and len(frames)==len(set(frames)) and ackseq==list(range(1,len(ackseq)+1)),
  "phase_stats":summary,"hold_differences":pairs,"physical_heading_validated":False,
  "notes":["Phase markers are operator labels, not proof that the stated action occurred.",
           "CAMERA_ONLY or AIM_ONLY independence needs independent visual and control verification.",
           "Cross-session offsets and zero-axis identity are not validated by per-session mathematical coherence."]}
def compare(sids,root=Path("output/csv")):
 reports=[audit(sid,root) for sid in sids]
 checks=["BASELINE_STILL","BODY_TURN_LEFT","BODY_TURN_RIGHT","MOVE_FORWARD_NO_TURN","AIM_ONLY","WEAPON_CHANGE","CAMERA_ONLY"]
 matrix=[{"sid":r["sid"],"complete":r["complete"],**{key:r["phase_stats"].get(key,{}).get("sum_steps_deg") for key in checks}} for r in reports]
 return {"sessions":matrix,"consistent_data_only":all(r["complete"] for r in reports),"physical_heading_validated":False}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("sid",nargs="+");p.add_argument("--root",type=Path,default=Path("output/csv"))
 a=p.parse_args()
 if len(a.sid)==1:
  data=audit(a.sid[0],a.root);out=a.root/f"bond_heading_hud_v1_9_6_{a.sid[0]}_audit.json"
 else:
  data=compare(a.sid,a.root);out=a.root/f"bond_heading_hud_v1_9_6_cross_session_{'_'.join(a.sid)}.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Bond heading v1.9.6 audit",out,"complete",data.get("complete",data.get("consistent_data_only")))
if __name__=="__main__":main()
