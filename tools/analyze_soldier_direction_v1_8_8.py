"""Directional axis identification v1.8.8: experimental, read-only offline."""
import argparse,csv,json,struct,math
from collections import defaultdict,Counter
from pathlib import Path
ORDER=["AXIS_A_POS","AXIS_A_NEG","AXIS_B_POS","AXIS_B_NEG","AXIS_A_REPEAT"]
CONTROLS=["BOND_ROTATE","BOND_MOVE","STATIONARY"]
def read(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def decode(v,fmt):
 try:
  n=struct.unpack(fmt,bytes.fromhex(v))[0]
  return float(n) if math.isfinite(n) and abs(n)<1e9 else None
 except (ValueError,struct.error):return None
def analyze(sid,root=Path("output/csv"),min_frames=30,quiet_epsilon=0.01):
 if not sid or ".." in sid or any(c in sid for c in "/\\\n\r"):raise ValueError("invalid session")
 stem=root/("soldier_direction_v1_8_8_"+sid)
 rows=read(Path(str(stem)+"_timeline.csv"))
 marks=read(Path(str(stem)+"_markers.csv"))
 ends=read(Path(str(stem)+"_termination.csv"))
 timeline=defaultdict(dict); phases={}
 for row in rows:
  if row["session"]!=sid:raise ValueError("wrong session")
  frame=int(row["frame"]);offset=int(row["offset_hex"],16)
  if offset in timeline[frame]:raise ValueError("duplicate frame/offset")
  timeline[frame][offset]=row["raw_be"]
  if frame in phases and phases[frame]!=row["phase"]:raise ValueError("mixed phase within frame")
  phases[frame]=row["phase"]
 frames=sorted(timeline)
 if not frames:raise ValueError("empty timeline")
 offsets=sorted(timeline[frames[0]])
 if any(sorted(timeline[f])!=offsets for f in frames):raise ValueError("incomplete frames")
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 grouped=defaultdict(list)
 for f in frames:grouped[phases[f]].append(f)
 marker_counts=Counter(x["label"] for x in marks)
 stats=[]
 for off in offsets:
  for fmt in (">f","<f"):
   observations={}
   for phase in ORDER+CONTROLS:
    ff=grouped.get(phase,[])
    vals=[decode(timeline[f][off],fmt) for f in ff]
    if len(vals)<min_frames or any(v is None for v in vals):
     observations[phase]={"available":False,"frames":len(ff)};continue
    # last minus first: phase may include preparation and transit, never an independent physical measurement
    delta=vals[-1]-vals[0]
    spread=max(vals)-min(vals)
    observations[phase]={"available":True,"frames":len(ff),"delta":delta,"spread":spread,"changes":sum(a!=b for a,b in zip(vals,vals[1:]))}
   a=observations.get("AXIS_A_POS",{});an=observations.get("AXIS_A_NEG",{})
   b=observations.get("AXIS_B_POS",{});bn=observations.get("AXIS_B_NEG",{})
   ready=all(x.get("available") for x in (a,an,b,bn))
   def opposite(x,y):
    return x["delta"]*y["delta"]<0 and abs(x["delta"])>quiet_epsilon and abs(y["delta"])>quiet_epsilon
   ap=ready and opposite(a,an);bp=ready and opposite(b,bn)
   ad=(abs(a["delta"])+abs(an["delta"]))/2 if ready else None
   bd=(abs(b["delta"])+abs(bn["delta"]))/2 if ready else None
   crossA=(bd/ad if ready and ad>quiet_epsilon else None)
   crossB=(ad/bd if ready and bd>quiet_epsilon else None)
   stationary=observations.get("STATIONARY",{})
   quiet=stationary.get("available") and stationary["spread"]<=quiet_epsilon
   repeat=observations.get("AXIS_A_REPEAT",{})
   repeated=bool(repeat.get("available") and a.get("available") and a["delta"]*repeat["delta"]>0)
   # Do not rank all values as coordinates. Only candidate with opposing directional responses.
   if ap or bp:
    stats.append({"offset_hex":f"0x{off:06X}","format":fmt,
      "axis_a_opposition":bool(ap),"axis_b_opposition":bool(bp),
      "axis_a_perpendicular_ratio":crossA,"axis_b_perpendicular_ratio":crossB,
      "stationary_quiet":bool(quiet),"axis_a_repeat_same_sign":repeated,
      "observations":observations})
 stats.sort(key=lambda x:(-int(x["axis_a_opposition"] and x["axis_a_perpendicular_ratio"] is not None and x["axis_a_perpendicular_ratio"]<0.25),
                        -int(x["axis_b_opposition"] and x["axis_b_perpendicular_ratio"] is not None and x["axis_b_perpendicular_ratio"]<0.25),
                        -int(x["stationary_quiet"]),x["offset_hex"]))
 return {"protocol":"soldier_directional_axis_v1_8_8","session":sid,"frames":len(frames),
   "capture_complete":bool(ends and ends[-1].get("reason")=="stop" and not gaps),
   "markers":marks,"missing_phases":[p for p in ORDER[:4] if len(grouped.get(p,[]))<min_frames],
   "gaps":gaps,"candidate_count":len(stats),"candidates":stats,
   "world_axes_validated":False,"soldier_identity_validated":False,"cross_save_validated":False,
   "limitations":["Directional phase labels are operator descriptions, not measured world axes.",
                  "End-minus-start may reflect transit/preparation and other changing game state.",
                  "Only selected aligned float32 BE/LE candidates are tested.",
                  "A correlated field is not necessarily physical position; repeat after a new save."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--min-frames",type=int,default=30);p.add_argument("--quiet-epsilon",type=float,default=0.01)
 a=p.parse_args();r=analyze(a.session,a.root,a.min_frames,a.quiet_epsilon)
 out=a.root/f"soldier_direction_v1_8_8_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Soldier direction v1.8.8",out,"frames",r["frames"],"candidates",r["candidate_count"],"complete",r["capture_complete"])
if __name__=="__main__":main()
