"""v1.5 read-only temporal calibration: trajectories and paired event lag, not angular calibration."""
import argparse,csv,re,struct,math
from pathlib import Path
PRIMARY=("0x0D3995","0x0D3D3D")
OFFSETS=PRIMARY+("0x0D3990","0x0D3994","0x0D3998","0x0D3D38","0x0D3D3C","0x0D3D40")
ACTIONS=("FIXED_NO_TARGET","FIXED_AIM_LEFT","FIXED_AIM_RIGHT","FIXED_AIM_CENTER",
         "TURN_LEFT_NO_TARGET","TURN_RIGHT_NO_TARGET","TURN_LEFT_AIM_OFF",
         "TURN_RIGHT_AIM_OFF","REST_AFTER_TURN")
FIELDS=("session","action","offset_hex","begin_frame","end_frame","samples","changes",
        "unique_values","first_raw","last_raw","first_float32_le","last_float32_le",
        "paired_exact_frame_events","paired_nearest_lag_median_frames","operator_camera_condition","status")
def read(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def floats(raw):
 v=struct.unpack("<f",bytes.fromhex(raw))[0]
 return v if math.isfinite(v) else None
def median(nums):
 s=sorted(nums);n=len(s)
 return None if not n else (s[(n-1)//2]+s[n//2])/2
def lag_summary(events_a,events_b,limit=8):
 if not events_a or not events_b:return 0,None
 bset=set(events_b)
 lags=[min((v-f for v in events_b if abs(v-f)<=limit),key=lambda x:(abs(x),x),default=None) for f in events_a]
 return len(set(events_a)&bset),median([x for x in lags if x is not None])
def analyze(markers,timeline,session):
 active=None;windows=[]
 for row in markers:
  if row.get("session")!=session:raise ValueError("marker session mismatch")
  label=row["label"];frame=int(row["frame"])
  if label=="STOP":
   if active is not None:raise ValueError("STOP while active")
   continue
  phase,sep,action=label.partition("_")
  if not sep or action not in ACTIONS:raise ValueError("bad label: "+label)
  if phase=="BEGIN":
   if active is not None:raise ValueError("nested marker")
   active=(action,frame)
  elif phase=="END":
   if active is None or active[0]!=action or frame<=active[1]:raise ValueError("unmatched end")
   windows.append((action,active[1],frame));active=None
  else:raise ValueError("invalid phase")
 if active is not None:raise ValueError("incomplete action")
 if not windows:raise ValueError("no complete actions")
 series={k:[] for k in OFFSETS}
 additional=set()
 for row in timeline:
  if row.get("session")!=session or not re.fullmatch("[0-9A-Fa-f]{8}",row.get("raw_hex","")):
   raise ValueError("invalid timeline row")
  key=row["offset_hex"]
  if not re.fullmatch(r"0x[0-9A-F]{6}",key):raise ValueError("invalid offset")
  if key not in series:series[key]=[];additional.add(key)
  series[key].append((int(row["frame"]),row["raw_hex"].upper()))
 output=[]
 for action,start,end in windows:
  selected={}
  for offset in series:
   seq=[(frame,val) for frame,val in series[offset] if start<=frame<=end]
   if len(seq)!=end-start+1 or any(f!=start+i for i,(f,_) in enumerate(seq)):
    raise ValueError("frame gap/reset in "+action+" "+offset)
   selected[offset]=seq
  changes={}
  for offset,seq in selected.items():
   changes[offset]=[seq[i][0] for i in range(1,len(seq)) if seq[i][1]!=seq[i-1][1]]
  simultaneous,lag=lag_summary(changes[PRIMARY[0]],changes[PRIMARY[1]])
  for offset,seq in selected.items():
   values=[v for _,v in seq]
   output.append(dict(session=session,action=action,offset_hex=offset,begin_frame=start,end_frame=end,
    samples=len(seq),changes=len(changes[offset]),unique_values=len(set(values)),
    first_raw=values[0],last_raw=values[-1],
    first_float32_le=floats(values[0]),last_float32_le=floats(values[-1]),
    paired_exact_frame_events=simultaneous,paired_nearest_lag_median_frames=lag,
    operator_camera_condition=("declared_fixed" if action.startswith("FIXED") or action=="REST_AFTER_TURN" else "declared_turning"),
    status="experimental_not_a_validated_heading_or_aim_symbol"))
 return output
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--directory",type=Path,default=Path("output"));a=p.parse_args()
 if not re.fullmatch("[A-Za-z0-9_]+",a.session):p.error("invalid session")
 stem=a.directory/"csv"/f"horizontal_v1_5_{a.session}"
 rows=analyze(read(Path(str(stem)+"_markers.csv")),read(Path(str(stem)+"_timeline.csv")),a.session)
 path=Path(str(stem)+"_calibration_audit.csv")
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 print("Wrote",path,"rows",len(rows))
 print("Only temporal contrasts and hypothetical numerical interpretations; no validated camera or aim heading.")
if __name__=="__main__":main()
