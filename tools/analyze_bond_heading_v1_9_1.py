"""Bond heading v1.9.1: offline retrospective and new vector audit (read only)."""
import argparse,csv,json,math,re,struct
from pathlib import Path
from collections import defaultdict
FIELDS=(0x0D33EC,0x0D33F0,0x0D33F4,0x0D33F8,0x0D33FC,0x0D3400,0x0D3404,0x0D3998,0x0D39A0,0x0D3D40,0x0D3D48)
def f32(raw):
 try:
  if raw is None or len(raw)!=8:return None
  v=struct.unpack(">f",bytes.fromhex(raw))[0]
  return v if math.isfinite(v) and abs(v)<1e8 else None
 except (ValueError,TypeError,struct.error):return None
def audit(sid,root=Path("output/csv"),source="v1.9"):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid SID")
 if source not in ("v1.9","v1.9.1"):raise ValueError("invalid source")
 stem=root/("bond_heading_"+("v1_9_" if source=="v1.9" else "v1_9_1_")+sid)
 def load(s):
  with Path(str(stem)+s).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 raw=defaultdict(dict);phase={}
 for row in load("_timeline.csv"):
  if row["session"]!=sid:raise ValueError("session mismatch")
  frame=int(row["frame"]);addr=int(row["offset_hex"],16)
  if addr in raw[frame]:raise ValueError("duplicate offset")
  if frame in phase and phase[frame]!=row["phase"]:raise ValueError("mixed frame phase")
  raw[frame][addr]=row["raw_be"].upper();phase[frame]=row["phase"]
 if not raw:raise ValueError("empty timeline")
 frames=sorted(raw)
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 end=load("_termination.csv")
 summaries={}
 for address in FIELDS:
  per={}
  for p in sorted(set(phase.values())):
   seq=[(n,raw[n][address]) for n in frames if phase[n]==p and address in raw[n]]
   if not seq:continue
   numbers=[f32(v) for _,v in seq]
   valid=all(v is not None for v in numbers)
   increments=[b-a for a,b in zip(numbers,numbers[1:])] if valid else []
   nonzero=[v for v in increments if v!=0]
   per[p]={"frames":len(seq),"raw_unique":len(set(v for _,v in seq)),
    "raw_changes":sum(a[1]!=b[1] for a,b in zip(seq,seq[1:])),
    "first_raw":seq[0][1],"last_raw":seq[-1][1],
    "first_float":numbers[0],"last_float":numbers[-1],
    "delta":numbers[-1]-numbers[0] if valid else None,
    "min":min(numbers) if valid else None,"max":max(numbers) if valid else None,
    "up_steps":sum(v>0 for v in nonzero),"down_steps":sum(v<0 for v in nonzero),
    "largest_step":max((abs(v) for v in nonzero),default=0) if valid else None}
  summaries[f"0x{address:06X}"]=per
 # Joint samples of candidate direction-vector components: check radial stability
 pairs=[]
 possible=[0x0D33F0,0x0D33F8,0x0D33FC,0x0D3400,0x0D3404]
 for i,a in enumerate(possible):
  for b in possible[i+1:]:
   xy=[(f32(raw[n].get(a)),f32(raw[n].get(b))) for n in frames if a in raw[n] and b in raw[n]]
   xy=[v for v in xy if None not in v]
   if len(xy)<2:continue
   radii=[math.hypot(*v) for v in xy]
   pairs.append({"a":f"0x{a:06X}","b":f"0x{b:06X}","samples":len(xy),
    "r2_min":min(v*v for v in radii),"r2_max":max(v*v for v in radii),
    "r2_mean":sum(v*v for v in radii)/len(radii),
    "r2_spread":max(v*v for v in radii)-min(v*v for v in radii)})
 pairs.sort(key=lambda p:(p["r2_spread"],abs(p["r2_mean"]-1)))
 # Compare fixed-offset correlated probes pointwise as a separate hypothesis
 offsets=[]
 for a,b in ((0x0D3998,0x0D3D40),(0x0D39A0,0x0D3D48)):
  ds=[]
  for n in frames:
   x=f32(raw[n].get(a));y=f32(raw[n].get(b))
   if x is not None and y is not None:ds.append(y-x)
  offsets.append({"a":f"0x{a:06X}","b":f"0x{b:06X}","samples":len(ds),
   "difference_min":min(ds) if ds else None,"difference_max":max(ds) if ds else None})
 return {"protocol":"bond_heading_v1_9_1","source":source,"session":sid,"frames":len(frames),
  "complete":bool(end and end[-1].get("reason")=="stop" and not gaps),
  "gaps":gaps,"fields":summaries,"vector_pair_hypotheses":pairs,
  "related_probe_differences":offsets,
  "heading_validated":False,"trig_encoding_validated":False,
  "caveats":["A direction-vector component is not proved by range [-1,1] alone.",
  "Radial invariance must also be tested over actual turning samples.",
  "End-of-phase return near baseline is not an independently measured 360-degree rotation.",
  "A control input can transiently move the camera or gun independent of character heading."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("sid")
 p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--source",choices=["v1.9","v1.9.1"],default="v1.9")
 a=p.parse_args();r=audit(a.sid,a.root,a.source)
 path=a.root/f"bond_heading_v1_9_1_{a.source.replace('.','_')}_{a.sid}_analysis.json"
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Heading vector audit",path,"frames",r["frames"],"complete",r["complete"])
if __name__=="__main__":main()
