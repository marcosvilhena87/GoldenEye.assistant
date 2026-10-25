"""v1.9.2 cycle and orthogonal component audit; exploratory, read-only."""
import argparse,csv,json,math,re,struct
from collections import defaultdict
from pathlib import Path
H=0x0D33F8
STOPS=("BASELINE_STILL","HOLD_90","HOLD_180","HOLD_270","HOLD_360","HOLD_R270","HOLD_R180","HOLD_R90","HOLD_ORIGIN","HOLD_MOVE")
TURNS=("TURN_LEFT_90","TURN_LEFT_180","TURN_LEFT_270","TURN_LEFT_360","TURN_RIGHT_270","TURN_RIGHT_180","TURN_RIGHT_90","TURN_RIGHT_0")
def number(raw):
 try:
  x=struct.unpack(">f",bytes.fromhex(raw))[0]
  return x if math.isfinite(x) and abs(x)<1e7 else None
 except (TypeError,ValueError,struct.error):return None
def analyze(sid,root=Path("output/csv"),source="v1.9.2"):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid session")
 if source not in ("v1.9.2","v1.9.1"):raise ValueError("invalid source")
 prefix="bond_heading_"+("v1_9_2_" if source=="v1.9.2" else "v1_9_1_")+sid
 def read(s):
  with (root/(prefix+s)).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
 timeline=read("_timeline.csv");ending=read("_termination.csv");markers=read("_markers.csv")
 values=defaultdict(dict);phases={}
 for row in timeline:
  if row["session"]!=sid:raise ValueError("session mismatch")
  n=int(row["frame"]);o=int(row["offset_hex"],16)
  if o in values[n]:raise ValueError("duplicate sample")
  if n in phases and phases[n]!=row["phase"]:raise ValueError("phase inconsistency")
  phases[n]=row["phase"];values[n][o]=row["raw_be"]
 if not values:raise ValueError("no samples")
 ordered=sorted(values)
 gaps=[[x,y] for x,y in zip(ordered,ordered[1:]) if y!=x+1]
 addresses=sorted({o for v in values.values() for o in v})
 summaries={}
 for p in sorted(set(phases.values())):
  samples=[n for n in ordered if phases[n]==p]
  data={}
  for o in addresses:
   vals=[(n,number(values[n].get(o))) for n in samples if o in values[n]]
   if not vals or any(v is None for _,v in vals):continue
   seq=[v for _,v in vals]
   delta=[b-a for a,b in zip(seq,seq[1:])]
   data[f"0x{o:06X}"]={"first":seq[0],"last":seq[-1],"span":max(seq)-min(seq),
      "changes":sum(x!=0 for x in delta),"up":sum(x>0 for x in delta),"down":sum(x<0 for x in delta)}
  summaries[p]={"frames":len(samples),"fields":data}
 # Select a conservative orthogonal candidate: minimum radial squared spread
 # among available turning frames, but also report the range and coordinate spans.
 turnframes=[n for n in ordered if phases[n] in TURNS and H in values[n] and number(values[n][H]) is not None]
 pairs=[]
 for other in addresses:
  if other==H:continue
  vals=[(number(values[n].get(H)),number(values[n].get(other)))
        for n in turnframes if other in values[n]]
  vals=[(x,y) for x,y in vals if x is not None and y is not None]
  if len(vals)<30:continue
  r2=[x*x+y*y for x,y in vals]
  xs=[x for x,y in vals];ys=[y for x,y in vals]
  pairs.append({"other":f"0x{other:06X}","samples":len(vals),
    "r2_min":min(r2),"r2_max":max(r2),"r2_spread":max(r2)-min(r2),
    "r2_mean":sum(r2)/len(r2),"x_span":max(xs)-min(xs),"y_span":max(ys)-min(ys),
    "candidate_unit_circle":max(r2)-min(r2)<0.02 and abs(sum(r2)/len(r2)-1)<0.02
     and max(xs)-min(xs)>0.5 and max(ys)-min(ys)>0.5})
 pairs.sort(key=lambda x:(not x["candidate_unit_circle"],x["r2_spread"],abs(x["r2_mean"]-1)))
 checkpoints=[]
 for p in STOPS:
  if p in summaries:
   val=summaries[p]["fields"].get(f"0x{H:06X}")
   if val:checkpoints.append({"phase":p,**val})
 return {"protocol":"bond_heading_v1_9_2","source":source,"session":sid,
  "frames":len(ordered),"complete":bool(ending and ending[-1].get("reason")=="stop" and not gaps),
  "gaps":gaps,"markers":markers,"phase_summary":summaries,
  "heading_checkpoints":checkpoints,"orthogonal_candidates":pairs,
  "heading_validated":False,"orthogonal_validated":False,
  "limitations":["Quadrants are operator estimates, not calibrated angles.",
    "A near-unit norm is a candidate filter, not sufficient evidence of heading.",
    "Sampling is once per frame; repeated/stationary samples are not independent.",
    "Second session, fixed landmarks, core/ROM identity and camera/weapon controls remain required."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session")
 p.add_argument("--source",choices=("v1.9.2","v1.9.1"),default="v1.9.2")
 p.add_argument("--root",type=Path,default=Path("output/csv"))
 a=p.parse_args();r=analyze(a.session,a.root,a.source)
 path=a.root/f"bond_heading_v1_9_2_{a.source.replace('.','_')}_{a.session}_analysis.json"
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Heading cycle v1.9.2",path,"frames",r["frames"],"complete",r["complete"],
       "pair candidates",len(r["orthogonal_candidates"]))
if __name__=="__main__":main()
