"""v1.3 camera/aim distinction: descriptive temporal evidence, read-only."""
import argparse,csv,re,struct,math
from pathlib import Path
OFFSETS=("0x0D3995","0x0D3D3D")
ACTIONS={"FIXED_CAMERA_ON_TARGET":"aim_candidate_with_camera_fixed",
"FIXED_CAMERA_OFF_TARGET":"target_motion_control_with_camera_fixed",
"FIXED_CAMERA_NO_TARGET":"no_target_control_with_camera_fixed",
"TURN_CAMERA_NO_TARGET":"camera_rotation_control",
"FIXED_CAMERA_CONTROL":"stationary_control"}
FIELDS=("session","action","hypothesis","offset_hex","begin_frame","end_frame","samples","changes",
"unique_values","first_hex","last_hex","first_float32_le","last_float32_le","camera_state","status")
def load(path):
 with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def interpret(raw):
 v=struct.unpack("<f",bytes.fromhex(raw))[0]
 return v if math.isfinite(v) else ""
def analyze(markers,timeline,sid):
 stack=None;windows=[]
 for row in markers:
  if row.get("session")!=sid:raise ValueError("Session mismatch")
  label=row["label"];frame=int(row["frame"])
  if label=="STOP":
   if stack:raise ValueError("STOP during interval")
   continue
  phase,sep,action=label.partition("_")
  if not sep or action not in ACTIONS:raise ValueError("Unexpected marker "+label)
  if phase=="BEGIN":
   if stack:raise ValueError("Nested action")
   stack=(action,frame)
  elif phase=="END":
   if not stack or stack[0]!=action or frame<=stack[1]:raise ValueError("Bad END")
   windows.append((action,stack[1],frame));stack=None
  else:raise ValueError("Unknown phase")
 if stack:raise ValueError("Unclosed interval")
 if not windows:raise ValueError("No complete intervals")
 series={o:[] for o in OFFSETS}
 for r in timeline:
  if r.get("session")!=sid or r.get("offset_hex") not in series or not re.fullmatch("[0-9A-Fa-f]{8}",r.get("raw_hex","")):
   raise ValueError("Invalid timeline row")
  series[r["offset_hex"]].append((int(r["frame"]),r["raw_hex"].upper()))
 results=[]
 for action,start,end in windows:
  for off in OFFSETS:
   data=[(f,b) for f,b in series[off] if start<=f<=end]
   if len(data)!=(end-start+1) or any(f!=start+i for i,(f,_) in enumerate(data)):
    raise ValueError("Incomplete/noncontiguous frame coverage; possible savestate or reset")
   seq=[b for _,b in data]
   results.append(dict(session=sid,action=action,hypothesis=ACTIONS[action],offset_hex=off,
     begin_frame=start,end_frame=end,samples=len(seq),
     changes=sum(a!=b for a,b in zip(seq,seq[1:])),unique_values=len(set(seq)),
     first_hex=seq[0],last_hex=seq[-1],first_float32_le=interpret(seq[0]),
     last_float32_le=interpret(seq[-1]),camera_state="operator_declared_fixed" if action.startswith("FIXED_") else "operator_declared_moving",
     status="descriptive_only_not_causality"))
 return results
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--directory",type=Path,default=Path("output"));a=p.parse_args()
 if not re.fullmatch("[A-Za-z0-9_]+",a.session):p.error("Bad session")
 stem=a.directory/"csv"/f"horizontal_v1_3_{a.session}"
 rows=analyze(load(Path(str(stem)+"_markers.csv")),load(Path(str(stem)+"_timeline.csv")),a.session)
 path=Path(str(stem)+"_camera_aim_audit.csv")
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 print("Wrote",path,"rows",len(rows))
 print("Camera state is operator-declared, NOT detected from a validated camera symbol.")
if __name__=="__main__":main()
