"""Spatial v2.3: reconstruct aligned fields from v2.2 window, offline only."""
import argparse,csv,math,re,struct,statistics
from pathlib import Path
from collections import defaultdict
PHASES=("STILL","MOVE","HOLD","ROTATE","ROTATE_HOLD")
START,END=0x3B30B0,0x3B30FF
HEAD=("session","offset","width","interpretation","still_n","move_n","hold_n",
      "rotate_n","rotate_hold_n","still_change_rate","move_change_rate",
      "hold_change_rate","rotate_change_rate","rotate_hold_change_rate",
      "still_range","move_range","hold_range","rotate_range","rotate_hold_range",
      "still_net","move_net","hold_net","rotate_net","rotate_hold_net",
      "movement_contrast","rotation_contrast","finite_fraction","evidence_for",
      "evidence_against","status")
BOUND=("session","boundary","offset","width","interpretation","before_median",
       "after_median","median_shift","first_after","last_before")
FORMATS={2:("u16", "i16"),4:("u32","i32","f32")}

def decode(data,kind,endian):
 fmt={"u16":"H","i16":"h","u32":"I","i32":"i","f32":"f"}[kind]
 return struct.unpack(endian+fmt,data)[0]

def read(path):
 with path.open(newline="",encoding="utf8") as file:return list(csv.DictReader(file))

def load(session,root):
 if not re.fullmatch(r"[A-Za-z0-9_]+",session):raise ValueError("Invalid session")
 base=root/"output/csv"/("spatial_v2_2_"+session)
 termination=read(Path(str(base)+"_termination.csv"))
 if len(termination)!=1 or termination[0].get("reason")!="stop":raise ValueError("Confirmed STOP required")
 marks=read(Path(str(base)+"_markers.csv"))
 if [m["label"] for m in marks]!=list(PHASES)+["STOP"]:raise ValueError("Invalid marker sequence")
 starts=[int(m["frame"]) for m in marks]
 if any(y<=x for x,y in zip(starts,starts[1:])):raise ValueError("Non-increasing markers")
 if read(Path(str(base)+"_discontinuities.csv")):raise ValueError("Timeline discontinuity")
 frame_map=defaultdict(dict)
 last=-1
 with Path(str(base)+"_window.csv").open(newline="",encoding="utf8") as file:
  for row in csv.DictReader(file):
   if row["session"]!=session:raise ValueError("Mixed session")
   f=int(row["frame"])
   if f<last:raise ValueError("Unordered frames")
   last=f
   address=int(row["offset"],16)
   if address<START or address>END or not re.fullmatch("[0-9A-Fa-f]{2}",row["byte_hex"]):
    raise ValueError("Invalid byte offset or value")
   if f<starts[0]:expected="PRESTART"
   elif f>=starts[-1]:raise ValueError("Sample after STOP")
   else:expected=next(PHASES[i] for i in range(len(PHASES)) if starts[i]<=f<starts[i+1])
   if row["phase"]!=expected:raise ValueError("Incorrect phase")
   if address in frame_map[f]:raise ValueError("Duplicate byte at frame")
   frame_map[f][address]=int(row["byte_hex"],16)
 for f in range(starts[0],starts[-1]):
  if f not in frame_map or len(frame_map[f])!=END-START+1:
   raise ValueError("Incomplete window at frame "+str(f))
 return frame_map,starts

def features(values):
 finite=[v for v in values if math.isfinite(v)]
 if not finite:return dict(n=len(values),rate=1,rng="",net="",median="",finite=0)
 rate=sum(a!=b for a,b in zip(values,values[1:]))/max(len(values)-1,1)
 # A single NaN or Inf blocks net-range comparison; don't silently discard.
 good=len(finite)==len(values)
 return dict(n=len(values),rate=rate,rng=max(finite)-min(finite) if good else "",
             net=values[-1]-values[0] if good else "",
             median=statistics.median(finite) if good else "",finite=len(finite)/len(values))

def audit(session,window,markers):
 summaries,boundaries=[],[]
 for width in (2,4):
  for offset in range(START,END-width+2,width):
   for endian_name,endian in (("be",">"),("le","<")):
    for kind in FORMATS[width]:
     name=endian_name+"_"+kind
     sections={}
     for i,phase in enumerate(PHASES):
      section=[]
      for frame in range(markers[i],markers[i+1]):
       blob=bytes(window[frame][offset+j] for j in range(width))
       section.append(decode(blob,kind,endian))
      sections[phase]=section
     f={p:features(v) for p,v in sections.items()}
     finite=min(f[p]["finite"] for p in PHASES)
     # Rates alone are evidence of activity, not of position or causality.
     move_contrast=f["MOVE"]["rate"]-max(f["STILL"]["rate"],f["HOLD"]["rate"])
     rot_contrast=f["ROTATE"]["rate"]-max(f["HOLD"]["rate"],f["ROTATE_HOLD"]["rate"])
     reasons_for=[];reasons_against=[]
     if finite==1 and move_contrast>=.15:reasons_for.append("movement_change_rate_increased")
     if finite==1 and rot_contrast>=.15:reasons_for.append("rotation_change_rate_increased")
     if max(f[p]["rate"] for p in ("STILL","HOLD","ROTATE_HOLD"))<=.05:
      reasons_for.append("hold_change_rate_low")
     if min(f[p]["rate"] for p in ("STILL","HOLD","ROTATE_HOLD"))>.5:
      reasons_against.append("all_holds_change_frequently")
     if finite<1:reasons_against.append("nonfinite_interpretations")
     if move_contrast<=0:reasons_against.append("no_movement_rate_increase")
     if rot_contrast<=0:reasons_against.append("no_rotation_rate_increase")
     record=dict(session=session,offset=f"0x{offset:06X}",width=width,
       interpretation=name,still_n=f["STILL"]["n"],move_n=f["MOVE"]["n"],
       hold_n=f["HOLD"]["n"],rotate_n=f["ROTATE"]["n"],
       rotate_hold_n=f["ROTATE_HOLD"]["n"],movement_contrast=move_contrast,
       rotation_contrast=rot_contrast,finite_fraction=finite,
       evidence_for=";".join(reasons_for),evidence_against=";".join(reasons_against),
       status="experimental_unverified")
     for p in PHASES:
      key=p.lower()
      record[key+"_change_rate"]=f[p]["rate"]
      record[key+"_range"]=f[p]["rng"]
      record[key+"_net"]=f[p]["net"]
     summaries.append(record)
     for i in range(1,len(PHASES)):
      left,right=PHASES[i-1],PHASES[i]
      before=sections[left][-min(30,len(sections[left])):]
      after=sections[right][:min(30,len(sections[right]))]
      median_before=statistics.median(before) if all(math.isfinite(v) for v in before) else ""
      median_after=statistics.median(after) if all(math.isfinite(v) for v in after) else ""
      boundaries.append(dict(session=session,boundary=left+"->"+right,
        offset=f"0x{offset:06X}",width=width,interpretation=name,
        before_median=median_before,after_median=median_after,
        median_shift=median_after-median_before if median_before!="" and median_after!="" else "",
        first_after=after[0],last_before=before[-1]))
 return summaries,boundaries

def run(session,root):
 window,markers=load(session,root)
 summaries,boundaries=audit(session,window,markers)
 base=root/"output/csv"/("spatial_v2_3_"+session)
 paths=[Path(str(base)+"_fields.csv"),Path(str(base)+"_boundaries.csv")]
 if any(p.exists() for p in paths):raise FileExistsError("Refusing overwrite of existing v2.3 results")
 for path,fields,rows in zip(paths,(HEAD,BOUND),(summaries,boundaries)):
  with path.open("x",newline="",encoding="utf8") as fh:
   writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader();writer.writerows(rows)
 return paths,(summaries,boundaries)

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("session");parser.add_argument("--root",type=Path,default=Path("."))
 a=parser.parse_args()
 paths,results=run(a.session,a.root.resolve())
 for p,rows in zip(paths,results):print("Wrote",p,"rows",len(rows))
 print("All reconstructed fields remain experimental_unverified.")
