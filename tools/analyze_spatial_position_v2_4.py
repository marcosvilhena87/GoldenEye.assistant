"""Spatial v2.4 offline controlled movement differential; never validates addresses."""
import argparse,csv,math,re,statistics,struct
from collections import defaultdict
from pathlib import Path
PHASES=("P0_HOLD","FORWARD","P1_HOLD","BACK","P0_RETURN_HOLD","ROTATE","P0_ROTATED_HOLD","FORWARD_AGAIN","P2_HOLD")
HOLDS=("P0_HOLD","P1_HOLD","P0_RETURN_HOLD","P0_ROTATED_HOLD","P2_HOLD")
START,END=0x3B30B0,0x3B30FF
FIELDS=("session","offset","width","type","p0_median","p1_median","return_median","rotated_median","p2_median",
"p0_mad","p1_mad","return_mad","rotated_mad","p2_mad",
"step1","step_back","return_error","rotation_shift","step2","direction_reversed","return_close","holds_stable","rotation_stable","status")
def read(path):
 with path.open(encoding="utf8",newline="") as f:return list(csv.DictReader(f))
def load(session,root):
 if not re.fullmatch(r"[A-Za-z0-9_]+",session):raise ValueError("Invalid session")
 stem="spatial_v2_4_"+session;folder=root/"output/csv"
 t=read(folder/(stem+"_termination.csv"))
 if len(t)!=1 or t[0].get("reason")!="stop":raise ValueError("Confirmed STOP required")
 if read(folder/(stem+"_discontinuities.csv")):raise ValueError("Timeline discontinuity")
 m=read(folder/(stem+"_markers.csv"))
 if [r["label"] for r in m]!=list(PHASES)+["STOP"]:raise ValueError("Wrong phase sequence")
 boundaries=[int(r["frame"]) for r in m]
 if any(b<=a for a,b in zip(boundaries,boundaries[1:])):raise ValueError("Bad markers")
 frames=defaultdict(dict);last=-1
 with (folder/(stem+"_window.csv")).open(encoding="utf8",newline="") as f:
  for r in csv.DictReader(f):
   if r["session"]!=session:raise ValueError("Mixed session")
   frame=int(r["frame"]);address=int(r["offset"],16)
   if frame<last:raise ValueError("Out of order")
   last=frame
   if not START<=address<=END or not re.fullmatch(r"[A-Fa-f0-9]{2}",r["byte_hex"]):raise ValueError("Bad byte")
   if frame<boundaries[0]:expected="PRESTART"
   elif frame>=boundaries[-1]:raise ValueError("Post STOP telemetry")
   else:expected=next(PHASES[i] for i in range(len(PHASES)) if boundaries[i]<=frame<boundaries[i+1])
   if r["phase"]!=expected or address in frames[frame]:raise ValueError("Phase mismatch or duplicate")
   frames[frame][address]=int(r["byte_hex"],16)
 for frame in range(boundaries[0],boundaries[-1]):
  if set(frames[frame])!=set(range(START,END+1)):raise ValueError("Incomplete frame "+str(frame))
 return frames,boundaries
def decode(blob,kind):
 return struct.unpack({"be_f32":">f","le_f32":"<f","be_i32":">i","be_u32":">I",
                      "be_i16":">h","be_u16":">H"}[kind],blob)[0]
def metrics(vals):
 if not vals or not all(math.isfinite(x) for x in vals):return None
 med=statistics.median(vals)
 mad=statistics.median(abs(x-med) for x in vals)
 return med,mad
def audit(session,frames,boundaries,tail=120):
 if tail<10:raise ValueError("Minimum 10 hold frames")
 phase_ranges={p:list(range(boundaries[i],boundaries[i+1])) for i,p in enumerate(PHASES)}
 output=[]
 for width,kinds in ((2,("be_i16","be_u16")),(4,("be_f32","le_f32","be_i32","be_u32"))):
  for offset in range(START,END-width+2,width):
   for kind in kinds:
    data={}
    for phase in HOLDS:
     f=phase_ranges[phase]
     if len(f)<tail:raise ValueError("Hold "+phase+" needs "+str(tail)+" frames")
     vals=[decode(bytes(frames[x][offset+j] for j in range(width)),kind) for x in f[-tail:]]
     data[phase]=metrics(vals)
    if any(v is None for v in data.values()):continue
    a,b,c,d,e=[data[p] for p in HOLDS]
    step1=b[0]-a[0];back=c[0]-b[0];step2=e[0]-d[0]
    scale=max(abs(step1),abs(back),abs(step2),1e-6)
    error=abs(c[0]-a[0]);rot=abs(d[0]-c[0])
    reversed_ok=step1*back<0 and min(abs(step1),abs(back))>1e-6
    stable=max(v[1] for v in data.values())<=scale*.02
    return_close=error<=scale*.1
    rotate_ok=rot<=scale*.1
    output.append(dict(session=session,offset=f"0x{offset:06X}",width=width,type=kind,
     p0_median=a[0],p1_median=b[0],return_median=c[0],rotated_median=d[0],p2_median=e[0],
     p0_mad=a[1],p1_mad=b[1],return_mad=c[1],rotated_mad=d[1],p2_mad=e[1],
     step1=step1,step_back=back,return_error=error,rotation_shift=rot,step2=step2,
     direction_reversed=reversed_ok,return_close=return_close,holds_stable=stable,
     rotation_stable=rotate_ok,status="experimental_candidate" if all((reversed_ok,stable,return_close,rotate_ok)) else "not_supported"))
 return output
def run(session,root,tail=120):
 frames,boundaries=load(session,root)
 rows=audit(session,frames,boundaries,tail)
 path=root/"output/csv"/("spatial_v2_4_"+session+"_differentials.csv")
 with path.open("x",encoding="utf8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 return path,rows
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("session")
 parser.add_argument("--root",type=Path,default=Path("."));parser.add_argument("--tail",type=int,default=120)
 a=parser.parse_args();p,rows=run(a.session,a.root.resolve(),a.tail)
 print("Wrote",p,"rows",len(rows));print("Experimental labels only; no coordinate validation")
