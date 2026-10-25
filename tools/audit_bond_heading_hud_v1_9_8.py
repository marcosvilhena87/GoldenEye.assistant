"""Offline differential audit: experimental camera pitch vs visible reticle, v1.9.8."""
import argparse,csv,json,math,re
from collections import defaultdict
from pathlib import Path

FIELDS=("auxf_0D3998","auxf_0D3D40","auxf_0D39A0","auxf_0D3D48")
RAW=("aux_0D3998","aux_0D3D40","aux_0D39A0","aux_0D3D48")
CAMERA=("CAMERA_PITCH_UP","CAMERA_PITCH_DOWN")
AIM=("AIM_MODE_PITCH_UP","AIM_MODE_PITCH_DOWN")
YAW=("BODY_TURN_LEFT","BODY_TURN_RIGHT","AIM_MODE_YAW_LEFT","AIM_MODE_YAW_RIGHT")
CONTROLS=("BASELINE_STILL","STRAFE_LEFT","STRAFE_RIGHT","WEAPON_CHANGE")
def number(row,key):
 try:
  x=float(row[key])
  return x if math.isfinite(x) else None
 except (ValueError,TypeError,KeyError):return None
def read(path):
 with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def audit(sid,root=Path("output/csv")):
 if not re.fullmatch(r"[a-zA-Z0-9_]+",sid):raise ValueError("bad session")
 base=root/f"bond_heading_hud_v1_9_8_{sid}"
 rows=read(Path(str(base)+"_samples.csv"))
 events=read(Path(str(base)+"_events.csv"))
 ending=read(Path(str(base)+"_termination.csv"))
 if not rows:raise ValueError("no samples")
 if any(r["session"]!=sid for r in rows+events+ending):raise ValueError("session mismatch")
 frames=[int(r["frame"]) for r in rows]
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 acks=[r for r in events if r["event"]!="STOP"]
 seq=[int(r["seq"]) for r in acks]
 ended=bool(ending and ending[-1]["reason"]=="stop" and events and events[-1]["event"]=="STOP")
 complete=ended and not gaps and len(frames)==len(set(frames)) and seq==list(range(1,len(seq)+1))
 segments=[]
 for r in rows:
  if not segments or segments[-1]["phase"]!=r["phase"]:
   segments.append({"phase":r["phase"],"rows":[]})
  segments[-1]["rows"].append(r)
 result=[]
 for i,segment in enumerate(segments):
  data=segment["rows"]
  fieldstats={}
  for field,raw in zip(FIELDS,RAW):
   finite=[number(r,field) for r in data]
   finite=[v for v in finite if v is not None]
   changes=sum(a[raw]!=b[raw] for a,b in zip(data,data[1:]))
   fieldstats[field]={"finite_frames":len(finite),"raw_changes":changes,
       "first":finite[0] if finite else None,"last":finite[-1] if finite else None,
       "range":max(finite)-min(finite) if finite else None,
       "delta":finite[-1]-finite[0] if finite else None,
       "constant":changes==0}
  angles=[number(r,"angle_deg") for r in data]
  good=[v for v in angles if v is not None]
  steps=[number(r,"step_deg") for r in data]
  heading=sum(v for v in steps if v is not None)
  result.append({"index":i,"phase":segment["phase"],"frames":len(data),
    "start_frame":int(data[0]["frame"]),"end_frame":int(data[-1]["frame"]),
    "heading_cumulative_step_deg":heading,"heading_changed":abs(heading)>0.01,
    "finite_heading_frames":len(good),"fields":fieldstats})
 phasegroups=defaultdict(list)
 for x in result:phasegroups[x["phase"]].append(x)
 contrasts=[]
 for field in FIELDS:
  def changes(phases):
   return sum(x["fields"][field]["raw_changes"] for s in phases for x in phasegroups.get(s,[]))
  def samples(phases):
   return sum(max(1,x["frames"]-1) for s in phases for x in phasegroups.get(s,[]))
  contrasts.append({"field":field,
    "camera_pitch_changes":changes(CAMERA),"aim_mode_vertical_changes":changes(AIM),
    "baseline_changes":changes(("BASELINE_STILL",)),
    "camera_change_rate":changes(CAMERA)/samples(CAMERA) if any(p in phasegroups for p in CAMERA) else None,
    "aim_change_rate":changes(AIM)/samples(AIM) if any(p in phasegroups for p in AIM) else None,
    "baseline_change_rate":changes(("BASELINE_STILL",))/samples(("BASELINE_STILL",)) if "BASELINE_STILL" in phasegroups else None})
 return {"version":"v1.9.8","sid":sid,"complete":complete,"frames":len(rows),
    "valid_heading_frames":sum(r["valid"]=="1" for r in rows),"ack_count":len(acks),
    "gaps":gaps,"segments":result,"differential_raw_activity":contrasts,
    "pitch_address_confirmed":False,"reticle_address_confirmed":False,
    "notes":["RAW activity or float correlation is not proof of camera pitch or reticle offset.",
      "Aim mode vertical affects both camera and on-screen reticle per operator.",
      "A candidate specific to reticle requires independent visual reference, additional memory discovery and repeat sessions.",
      "A phase name or ACK does not establish a physical action."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("sid");p.add_argument("--root",type=Path,default=Path("output/csv"))
 a=p.parse_args();r=audit(a.sid,a.root)
 dest=a.root/f"bond_heading_hud_v1_9_8_{a.sid}_audit.json"
 if dest.exists():raise FileExistsError(dest)
 dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Bond heading v1.9.8",dest,"frames",r["frames"],"complete",r["complete"])
if __name__=="__main__":main()
