"""v1.9.9 offline temporal signal audit for camera pitch / reticle candidates.

Accepts v1.9.8 or v1.9.9 recordings, without altering historical captures.
"""
import argparse
import csv
import json
import math
import re
from pathlib import Path

FIELDS=("0D3998","0D3D40","0D39A0","0D3D48")
PAIRS=(("0D3998","0D3D40"),("0D39A0","0D3D48"))
PHASES=("CAMERA_PITCH_UP","CAMERA_PITCH_DOWN","AIM_MODE_PITCH_UP","AIM_MODE_PITCH_DOWN")
def principal(x):return (x+180)%360-180
def read(p):
 with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def val(r,key):
 try:
  a=float(r[key])
  return a if math.isfinite(a) else None
 except (ValueError,KeyError,TypeError):return None
def audit(sid,root=Path("output/csv"),version="v1_9_9",eps=1e-5):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid session id")
 if version not in ("v1_9_8","v1_9_9"):raise ValueError("invalid version")
 stem=root/f"bond_heading_hud_{version}_{sid}"
 samples=read(Path(str(stem)+"_samples.csv"))
 events=read(Path(str(stem)+"_events.csv"))
 ends=read(Path(str(stem)+"_termination.csv"))
 if not samples:raise ValueError("no samples")
 if any(r["session"]!=sid for r in samples+events+ends):raise ValueError("session mismatch")
 frames=[int(r["frame"]) for r in samples]
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 acks=[e for e in events if e["event"]!="STOP"]
 seq=[int(x["seq"]) for x in acks]
 complete=(bool(ends and ends[-1]["reason"]=="stop" and events and events[-1]["event"]=="STOP")
           and not gaps and len(set(frames))==len(frames) and seq==list(range(1,len(seq)+1)))
 runs=[]
 for r in samples:
  if not runs or runs[-1]["phase"]!=r["phase"]:runs.append({"phase":r["phase"],"rows":[]})
  runs[-1]["rows"].append(r)
 out=[]
 for i,run in enumerate(runs):
  rows=run["rows"]
  rec={"index":i,"phase":run["phase"],"start_frame":int(rows[0]["frame"]),
       "end_frame":int(rows[-1]["frame"]),"frames":len(rows),"signals":{},"pairs":{}}
  for name in FIELDS:
   rawkey="aux_"+name
   floatkey="auxf_"+name
   values=[val(r,floatkey) for r in rows]
   change_indices=[j for j in range(1,len(rows)) if rows[j][rawkey]!=rows[j-1][rawkey]]
   finite=[x for x in values if x is not None]
   baseline=values[0]
   active=[j for j,x in enumerate(values) if x is not None and baseline is not None and abs(x-baseline)>eps]
   first=change_indices[0] if change_indices else None
   last=change_indices[-1] if change_indices else None
   rec["signals"][name]={
    "first_value":values[0],"last_value":values[-1],
    "min":min(finite) if finite else None,"max":max(finite) if finite else None,
    "range":max(finite)-min(finite) if finite else None,
    "delta":values[-1]-values[0] if values[0] is not None and values[-1] is not None else None,
    "raw_change_count":len(change_indices),"first_change_frame":int(rows[first]["frame"]) if first is not None else None,
    "last_change_frame":int(rows[last]["frame"]) if last is not None else None,
    "first_departure_frame":int(rows[active[0]]["frame"]) if active else None,
    "last_departure_frame":int(rows[active[-1]]["frame"]) if active else None,
    "returned_to_start":abs(values[-1]-baseline)<=eps if baseline is not None and values[-1] is not None else None,
    "finite_frames":len(finite)}
  for left,right in PAIRS:
   matched=sum(rows[j]["aux_"+left]==rows[j]["aux_"+right] for j in range(len(rows)))
   lv=[val(r,"auxf_"+left) for r in rows];rv=[val(r,"auxf_"+right) for r in rows]
   diffs=[y-x for x,y in zip(lv,rv) if x is not None and y is not None]
   rec["pairs"][left+"_"+right]={"identical_raw_frames":matched,
     "identical_raw_fraction":matched/len(rows),
     "float_delta_range":max(diffs)-min(diffs) if diffs else None,
     "constant_float_offset":(max(diffs)-min(diffs)<=eps) if diffs else None}
  angles=[val(r,"angle_deg") for r in rows]
  steps=[val(r,"step_deg") for r in rows]
  rec["heading"]={"sum_step_deg":sum(x for x in steps if x is not None),
                  "valid_angles":sum(x is not None for x in angles)}
  out.append(rec)
 contrasts={}
 for p in PHASES:
  contrasts[p]=[{"index":x["index"],"frames":x["frames"],
                  "ranges":{k:x["signals"][k]["range"] for k in FIELDS},
                  "changes":{k:x["signals"][k]["raw_change_count"] for k in FIELDS}}
                 for x in out if x["phase"]==p]
 return {"version":"v1.9.9","source_capture_version":version,"sid":sid,
  "complete":complete,"frames":len(samples),"valid_heading_frames":sum(r["valid"]=="1" for r in samples),
  "gaps":gaps,"ack_count":len(acks),"epsilon":eps,"segments":out,"contrasts":contrasts,
  "camera_pitch_validated":False,"reticle_offset_validated":False,
  "limitations":["Per-phase return-to-start is not a physical camera-return proof.",
   "Transient values and identical pair variations are correlations only.",
   "For repeatability use second session and independently labeled visual landmarks."]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("sid");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--source-version",choices=["v1_9_8","v1_9_9"],default="v1_9_9")
 p.add_argument("--epsilon",type=float,default=1e-5)
 a=p.parse_args()
 if not math.isfinite(a.epsilon) or a.epsilon<=0: p.error("epsilon must be finite and positive")
 result=audit(a.sid,a.root,a.source_version,a.epsilon)
 destination=a.root/f"bond_heading_hud_v1_9_9_{a.sid}_temporal_audit.json"
 if destination.exists():raise FileExistsError(destination)
 destination.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(f"v1.9.9 temporal audit: {destination} frames={result['frames']} complete={result['complete']}")
if __name__=="__main__":main()
