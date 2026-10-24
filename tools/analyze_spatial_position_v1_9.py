"""Spatial v1.9 candidate validation report (observations, never automatic promotion)."""
import argparse,csv,math,statistics,re
from collections import defaultdict
from pathlib import Path
FIELDS=("address","baseline_median","forward_first","forward_last","forward_delta","back_first","back_last","back_delta","return_error","forward_hold_range","back_hold_range","rotate_delta","rotate_hold_range","strafe_delta","reversed","holds_stable","rotation_stable","classification")
ADDRS=("0x3B30D8","0x3B30D0")
PHASES=("BASELINE_HOLD","FORWARD","FORWARD_HOLD","BACK","BACK_HOLD","ROTATE","ROTATE_HOLD","STRAFE","STRAFE_HOLD","STOP")
def readcsv(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def summary(values):
 return (values[0],values[-1],max(values)-min(values),statistics.median(values))
def evaluate(samples,threshold=0.01,hold_ratio=.05,rotation_ratio=.05):
 grouped=defaultdict(list)
 for r in samples:
  if r["phase"] not in PHASES[:-1] or r["address"] not in ADDRS:raise ValueError("Unexpected phase or address")
  try:v=float(r["be_float32"])
  except ValueError:raise ValueError("Non-finite float32 reading")
  if not math.isfinite(v):raise ValueError("Non-finite float32 reading")
  grouped[(r["address"],r["phase"])].append(v)
 out=[]
 for addr in ADDRS:
  data={phase:grouped[(addr,phase)] for phase in PHASES[:-1]}
  if not all(len(v)>=3 for v in data.values()):raise ValueError("At least 3 readings per phase and address required")
  base=summary(data["BASELINE_HOLD"])[3]
  f0,f1,_,_=summary(data["FORWARD"])
  b0,b1,_,_=summary(data["BACK"])
  fh=summary(data["FORWARD_HOLD"])
  bh=summary(data["BACK_HOLD"])
  ro=summary(data["ROTATE"])
  rh=summary(data["ROTATE_HOLD"])
  st=summary(data["STRAFE"])
  fd=f1-f0;bd=b1-b0
  scale=max(abs(fd),abs(bd),threshold)
  reverse=fd*bd<0 and min(abs(fd),abs(bd))>=threshold
  holds=fh[2]<=max(threshold,scale*hold_ratio) and bh[2]<=max(threshold,scale*hold_ratio)
  rot=ro[1]-ro[0]
  rotstable=abs(rot)<=max(threshold,scale*rotation_ratio)
  label="rejected_by_observations"
  if reverse and holds and rotstable:label="candidate_reproduced_unverified"
  elif reverse and holds:label="rotation_sensitive_unverified"
  elif reverse:label="directional_only_unverified"
  out.append(dict(address=addr,baseline_median=base,forward_first=f0,forward_last=f1,forward_delta=fd,
   back_first=b0,back_last=b1,back_delta=bd,return_error=abs(bh[3]-base),
   forward_hold_range=fh[2],back_hold_range=bh[2],rotate_delta=rot,
   rotate_hold_range=rh[2],strafe_delta=st[1]-st[0],
   reversed=reverse,holds_stable=holds,rotation_stable=rotstable,classification=label))
 return out
def run(session,root):
 if not re.fullmatch(r"[A-Za-z0-9_]+",session):raise ValueError("Invalid session")
 stem="spatial_v1_9_"+session
 folder=root/"output/csv"
 term=readcsv(folder/(stem+"_termination.csv"))
 if len(term)!=1 or term[0]["reason"]!="stop":raise ValueError("STOP confirmation required")
 markers=readcsv(folder/(stem+"_markers.csv"))
 if [r["label"] for r in markers]!=list(PHASES):raise ValueError("Complete marker sequence required")
 rows=readcsv(folder/(stem+"_samples.csv"))
 if not rows:raise ValueError("No telemetry")
 frames=[int(r["frame"]) for r in rows]
 if any(b<a for a,b in zip(frames,frames[1:])):raise ValueError("Non-monotonic frames")
 for r in rows:
  if r["session"]!=session:raise ValueError("Mixed session")
  if r["address"] not in ADDRS or not re.fullmatch(r"[0-9A-F]{8}",r["raw_be"]):raise ValueError("Malformed sample")
  if r["phase"] not in ("PRESTART",)+PHASES[:-1]:raise ValueError("Unexpected phase")
 if readcsv(folder/(stem+"_discontinuities.csv")):raise ValueError("Discontinuity detected")
 # PRESTART is valid read-only telemetry emitted before BASELINE_HOLD.
 # Never include it in experimental phase metrics.
 first_marker_frame=int(markers[0]["frame"])
 for r in rows:
  if r["phase"]=="PRESTART" and int(r["frame"])>=first_marker_frame:
   raise ValueError("PRESTART found after BASELINE_HOLD")
  if r["phase"]!="PRESTART" and int(r["frame"])<first_marker_frame:
   raise ValueError("Experimental phase before first marker")
 result=evaluate([r for r in rows if r["phase"]!="PRESTART"])
 dest=folder/(stem+"_validation.csv")
 with dest.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(result)
 return dest,result
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("."))
 args=p.parse_args()
 path,rows=run(args.session,args.root.resolve())
 print("Wrote",path)
 for r in rows:print(r["address"],r["classification"],"forward",r["forward_delta"],"back",r["back_delta"],"rotate",r["rotate_delta"])
 print("All classifications remain experimental. Labels do not verify player inputs.")
if __name__=="__main__":main()
