"""v1.8.11: isolate rotation components with/without auto-aim; observational."""
import argparse,csv,json,math,struct
from collections import defaultdict
from pathlib import Path
BOND=(0x06D248,0x06D250,0x0D33EC,0x0D33F4)
SOLDIER=(0x20F594,0x20F5AC,0x20F578,0x20F580,0x06A120,0x06A128)
PAIRS={"historical":((0x06D248,0x06D250),(0x20F594,0x20F5AC)),
       "alternate":((0x06D248,0x06D250),(0x20F578,0x20F580)),
       "alias":((0x0D33EC,0x0D33F4),(0x20F594,0x20F5AC))}
PHASES=("BOND_STOP_NEAR","BOND_ROTATE","BOND_STOP_FAR","AIM_ON_STILL","AIM_ON_ROTATE",
        "AIM_ON_SETTLE","AIM_OFF_STILL","AIM_OFF_ROTATE","AIM_OFF_SETTLE")
def decode(word):
 try:
  v=struct.unpack(">f",bytes.fromhex(word))[0]
  return v if math.isfinite(v) and abs(v)<1e8 else None
 except (struct.error,ValueError,TypeError):return None
def analyze(sid,root=Path("output/csv"),source="v1.8.11",min_frames=30):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid session")
 if min_frames<2:raise ValueError("min_frames must >=2")
 prefix="soldier_autoaim_v1_8_11_" if source=="v1.8.11" else "soldier_frozen_v1_8_10_"
 if source not in ("v1.8.10","v1.8.11"):raise ValueError("invalid source")
 path=Path(root)/(prefix+sid+"_timeline.csv")
 samples=defaultdict(dict);phase={}
 with path.open(newline="",encoding="utf-8") as handle:
  for row in csv.DictReader(handle):
   if row["session"]!=sid:raise ValueError("mixed sessions")
   n=int(row["frame"]);o=int(row["offset_hex"],16)
   if o in samples[n]:raise ValueError("duplicate value")
   samples[n][o]=row["raw_be"]
   if n in phase and phase[n]!=row["phase"]:raise ValueError("mixed phase")
   phase[n]=row["phase"]
 if not samples:raise ValueError("empty timeline")
 frames=sorted(samples)
 phases_seen=defaultdict(list)
 for n in frames:phases_seen[phase[n]].append(n)
 fields={}
 for off in (*BOND,*SOLDIER):
  field={}
  for p in PHASES:
   series=[(n,decode(samples[n].get(off))) for n in phases_seen[p]]
   valid=[(n,v) for n,v in series if v is not None]
   if len(valid)<min_frames:continue
   vs=[v for _,v in valid]
   field[p]={"frames":len(valid),"first":vs[0],"last":vs[-1],"signed_delta":vs[-1]-vs[0],
     "spread":max(vs)-min(vs),"changes":sum(a!=b for a,b in zip(vs,vs[1:]))}
  fields[f"0x{off:06X}"]=field
 distance={}
 for label,(bond,soldier) in PAIRS.items():
  metrics={}
  for p in PHASES:
   rows=[]
   for n in phases_seen[p]:
    decoded=[decode(samples[n].get(o)) for o in (*bond,*soldier)]
    if any(x is None for x in decoded):continue
    ba,bb,sa,sb=decoded
    rows.append((n,math.hypot(sa-ba,sb-bb)))
   if len(rows)>=min_frames:
    values=[v for _,v in rows]
    metrics[p]={"frames":len(rows),"first":values[0],"last":values[-1],"spread":max(values)-min(values)}
  distance[label]=metrics
 comparison={}
 for on,off in (("AIM_ON_STILL","AIM_OFF_STILL"),("AIM_ON_ROTATE","AIM_OFF_ROTATE"),
                ("AIM_ON_SETTLE","AIM_OFF_SETTLE")):
  comparison[on+"_vs_"+off]={key:{"on_spread":value.get(on,{}).get("spread"),
                                  "off_spread":value.get(off,{}).get("spread")}
                               for key,value in fields.items()}
 return {"protocol":"soldier_autoaim_rotation_isolation_v1_8_11","source":source,
  "session":sid,"frames":len(frames),"phase_frame_counts":{p:len(phases_seen[p]) for p in PHASES},
  "fields":fields,"distance_candidates":distance,"on_off_field_comparison":comparison,
  "autoaim_effect_validated":False,"physical_coordinates_validated":False,
  "limitations":["Auto-aim ON/OFF states must be confirmed independently by operator.",
    "The collector records no verified game auto-aim flag or input activity.",
    "Rotation phases may include motion, collision or settling; phase labels are observational.",
    "V1.8.10 retrospective analysis cannot compare auto-aim ON vs OFF.",
    "Rotational response does not alone distinguish physical position from a camera-related field."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--source",choices=("v1.8.10","v1.8.11"),default="v1.8.11");a=p.parse_args()
 report=analyze(a.session,a.root,a.source)
 out=a.root/f"soldier_autoaim_v1_8_11_{a.source.replace('.','_')}_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Autoaim rotation v1.8.11",out,"frames",report["frames"])
if __name__=="__main__":main()
