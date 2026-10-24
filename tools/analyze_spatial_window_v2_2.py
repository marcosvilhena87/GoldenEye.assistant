"""Offline neighboring byte-change rates for v2.2 optional collector."""
import argparse,csv,re
from collections import Counter,defaultdict
from pathlib import Path
FIELDS=("session","phase","offset","samples","unique","transitions","change_rate",
        "longest_run","top_raw","top_raw_fraction")
PHASES=("STILL","MOVE","HOLD","ROTATE","ROTATE_HOLD")
def read(path):
 with path.open(encoding="utf8",newline="") as f:return list(csv.DictReader(f))
def run(session,root):
 if not re.fullmatch(r"[A-Za-z0-9_]+",session):raise ValueError("Invalid session")
 folder=root/"output/csv";stem="spatial_v2_2_"+session
 term=read(folder/(stem+"_termination.csv"))
 if len(term)!=1 or term[0]["reason"]!="stop":raise ValueError("STOP required")
 marks=read(folder/(stem+"_markers.csv"))
 if [r["label"] for r in marks]!=list(PHASES)+["STOP"]:raise ValueError("Invalid markers")
 if read(folder/(stem+"_discontinuities.csv")):raise ValueError("Timeline discontinuity")
 markers=[int(r["frame"]) for r in marks]
 values=defaultdict(list);frames=defaultdict(list)
 for r in read(folder/(stem+"_window.csv")):
  if r["session"]!=session:raise ValueError("Mixed session")
  f=int(r["frame"]);offset=r["offset"]
  if not re.fullmatch(r"0x[0-9A-F]{6}",offset) or not re.fullmatch(r"[0-9A-F]{2}",r["byte_hex"]):
   raise ValueError("Malformed byte")
  if f<markers[0]:
   if r["phase"]!="PRESTART":raise ValueError("PRESTART mismatch")
   continue
  if f>=markers[-1]:raise ValueError("Samples after STOP")
  expected=next(PHASES[i] for i in range(len(PHASES)) if markers[i]<=f<markers[i+1])
  if r["phase"]!=expected:raise ValueError("Phase mismatch")
  key=(expected,offset)
  values[key].append(r["byte_hex"]);frames[key].append(f)
 rows=[]
 for phase in PHASES:
  offsets=sorted(k[1] for k in values if k[0]==phase)
  if not offsets:raise ValueError("Empty phase")
  for offset in offsets:
   key=(phase,offset);v=values[key];fs=frames[key]
   if fs!=list(range(markers[PHASES.index(phase)],markers[PHASES.index(phase)+1])):
    raise ValueError("Missing or duplicated samples")
   changes=sum(a!=b for a,b in zip(v,v[1:]))
   streak=best=1
   for a,b in zip(v,v[1:]):
    streak=streak+1 if a==b else 1;best=max(best,streak)
   raw,count=Counter(v).most_common(1)[0]
   rows.append(dict(session=session,phase=phase,offset=offset,samples=len(v),
    unique=len(set(v)),transitions=changes,change_rate=changes/max(1,len(v)-1),
    longest_run=best,top_raw=raw,top_raw_fraction=count/len(v)))
 path=folder/(stem+"_window_summary.csv")
 with path.open("x",newline="",encoding="utf8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 return path,rows
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("."))
 a=p.parse_args();path,rows=run(a.session,a.root.resolve())
 print("Wrote",path,"rows="+str(len(rows)),"; no coordinate validation")
