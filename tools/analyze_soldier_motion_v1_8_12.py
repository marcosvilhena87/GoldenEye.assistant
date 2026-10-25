"""v1.8.12: observational field response to Bond rotation vs translation."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path

BOND=(0x06D248,0x06D250,0x0D33EC,0x0D33F4)
SOLDIER=(0x20F594,0x20F5AC,0x20F578,0x20F580,0x06A120,0x06A128)
STILL=("STILL_BEFORE","STILL_AFTER_LEFT","STILL_AFTER_RIGHT","STILL_AFTER_FORWARD","STILL_AFTER_BACK","STILL_FINAL")
ROTATION=("ROTATE_LEFT","ROTATE_RIGHT","ROTATE_REPEAT")
TRANSLATION=("TRANSLATE_FORWARD","TRANSLATE_BACK")
PHASES=STILL+ROTATION+TRANSLATION
PAIRS={"historical":((0x06D248,0x06D250),(0x20F594,0x20F5AC)),
       "alternate":((0x06D248,0x06D250),(0x20F578,0x20F580)),
       "duplicate_region":((0x06D248,0x06D250),(0x06A120,0x06A128))}
def decode(value):
 try:
  n=struct.unpack(">f",bytes.fromhex(value))[0]
  return n if math.isfinite(n) and abs(n)<1e8 else None
 except (TypeError,ValueError,struct.error):return None
def phase_metrics(values,minimum):
 if len(values)<minimum:return {"available":False,"frames":len(values)}
 v=[x[1] for x in values]
 return {"available":True,"frames":len(values),"start_frame":values[0][0],"end_frame":values[-1][0],
         "first":v[0],"last":v[-1],"delta":v[-1]-v[0],"spread":max(v)-min(v),
         "changes":sum(a!=b for a,b in zip(v,v[1:])),
         "path_length":sum(abs(b-a) for a,b in zip(v,v[1:]))}
def analyze(sid,root=Path("output/csv"),minimum_frames=30):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid session")
 if minimum_frames<2:raise ValueError("invalid minimum_frames")
 stem=Path(root)/("soldier_motion_v1_8_12_"+sid)
 def csvrows(suffix):
  with Path(str(stem)+suffix).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 timeline=csvrows("_timeline.csv");markers=csvrows("_markers.csv");termination=csvrows("_termination.csv")
 if not timeline:raise ValueError("empty timeline")
 frames=defaultdict(dict);phase={}
 for row in timeline:
  if row["session"]!=sid:raise ValueError("foreign session")
  n=int(row["frame"]);offset=int(row["offset_hex"],16)
  if offset in frames[n]:raise ValueError("duplicate offset/frame")
  frames[n][offset]=row["raw_be"]
  if n in phase and phase[n]!=row["phase"]:raise ValueError("different phases within frame")
  phase[n]=row["phase"]
 ordered=sorted(frames)
 gaps=[[a,b] for a,b in zip(ordered,ordered[1:]) if b!=a+1]
 per_phase=defaultdict(list)
 for n in ordered:per_phase[phase[n]].append(n)
 field_results={}
 for offset in (*BOND,*SOLDIER):
  field={}
  for p in PHASES:
   valid=[]
   for n in per_phase[p]:
    v=decode(frames[n].get(offset))
    if v is not None:valid.append((n,v))
   field[p]=phase_metrics(valid,minimum_frames)
  field_results[f"0x{offset:06X}"]=field
 candidate_pairs={}
 for label,(bond,soldier) in PAIRS.items():
  result={}
  for p in PHASES:
   coords=[];raws=[]
   for n in per_phase[p]:
    addresses=(*bond,*soldier)
    values=[decode(frames[n].get(offset)) for offset in addresses]
    if any(v is None for v in values):continue
    bx,by,sx,sy=values
    coords.append((n,math.hypot(sx-bx,sy-by)))
    raws.append((frames[n][soldier[0]],frames[n][soldier[1]]))
   result[p]=phase_metrics(coords,minimum_frames)
   result[p]["soldier_raw_constant"]=bool(raws and len(set(raws))==1) if result[p]["available"] else None
  frozen_raws=[]
  for n in ordered:
   if phase[n] not in PHASES:continue
   if all(o in frames[n] for o in soldier):
    frozen_raws.append((frames[n][soldier[0]],frames[n][soldier[1]]))
  stable=bool(frozen_raws and len(set(frozen_raws))==1)
  # A strict, explicit negative control; no physical claims.
  rotations=[result[p] for p in ROTATION if result[p]["available"]]
  translations=[result[p] for p in TRANSLATION if result[p]["available"]]
  stills=[result[p] for p in STILL if result[p]["available"]]
  quiet_reference=max((p["spread"] for p in stills),default=None)
  candidate_pairs[label]={"bond_offsets":[f"0x{x:06X}" for x in bond],
    "soldier_offsets":[f"0x{x:06X}" for x in soldier],
    "phase_metrics":result,"soldier_constant_across_phases":stable,
    "max_still_spread":quiet_reference,
    "max_rotation_spread":max((p["spread"] for p in rotations),default=None),
    "max_translation_spread":max((p["spread"] for p in translations),default=None),
    "rotation_response_present":bool(rotations and quiet_reference is not None and any(p["spread"]>quiet_reference+0.01 for p in rotations)),
    "translation_response_present":bool(translations and quiet_reference is not None and any(p["spread"]>quiet_reference+0.01 for p in translations)),
    "support_level":"experimental_observational_only"}
 aliases={}
 for a,b in ((0x06D248,0x0D33EC),(0x06D250,0x0D33F4),
             (0x20F578,0x06A120),(0x20F580,0x06A128)):
  valid=[n for n in ordered if a in frames[n] and b in frames[n]]
  aliases[f"0x{a:06X}__0x{b:06X}"]={"frames_compared":len(valid),
      "equal_fraction":sum(frames[n][a]==frames[n][b] for n in valid)/len(valid) if valid else None}
 return {"protocol":"soldier_bond_motion_v1_8_12","session":sid,"frames":len(ordered),
   "capture_complete":bool(termination and termination[-1].get("reason")=="stop" and not gaps),
   "gaps":gaps,"markers":markers,"phase_frame_counts":{p:len(per_phase[p]) for p in PHASES},
   "fields":field_results,"candidate_pairs":candidate_pairs,"raw_alias_equalities":aliases,
   "physical_coordinates_validated":False,"bond_translation_verified":False,
   "bond_rotation_only_verified":False,"soldier_identity_validated":False,
   "limitations":["No controller input, facing-angle or independent world-position ground truth recorded.",
    "Phase names describe operator intended actions; camera rotation can coincide with motion.",
    "Float32 BE is a candidate interpretation; numeric changes are not physical distances.",
    "Frozen values do not prove a particular Soldier #1 identity.",
    "Movement may cross collisions or trigger camera/autoaim effects.",
    "Repeat across a new save and verify motion externally before promoting offsets."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--minimum-frames",type=int,default=30);a=p.parse_args()
 report=analyze(a.session,a.root,a.minimum_frames)
 out=a.root/f"soldier_motion_v1_8_12_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Bond motion v1.8.12",out,"frames",report["frames"],"complete",report["capture_complete"])
if __name__=="__main__":main()
