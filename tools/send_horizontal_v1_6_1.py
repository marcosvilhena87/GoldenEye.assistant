"""Atomic, bracketed v1.6.1 marker sender; confirms creation, NOT Lua consumption."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIONS=("MANUAL_ALIGNMENT","STATIONARY_TARGET","STATIONARY_TARGET_AIM_OFF","FIXED_AIM_DISABLED","FIXED_AIM_ENABLED","FIXED_AIM_WITH_TARGET","FIXED_AIM_NO_TARGET","NEW_SCENE_BASELINE","FIXED_NO_TARGET","FIXED_AIM_LEFT","FIXED_AIM_RIGHT","FIXED_AIM_CENTER","TURN_LEFT_NO_TARGET","TURN_RIGHT_NO_TARGET","TURN_LEFT_AIM_OFF","TURN_RIGHT_AIM_OFF","REST_AFTER_TURN")
LABELS={"STOP"}|{f"{p}_{a}" for a in ACTIONS for p in ("BEGIN","END")}
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Unknown label")
 sid=(root/"output/sessions/horizontal_v1_6_1_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 folder=root/"output/commands"
 term=root/"output/csv"/f"horizontal_v1_6_1_{sid}_termination.csv"
 if term.exists() and len(term.read_text(encoding="utf-8").splitlines())>1:raise RuntimeError("Collector already terminated; start fresh Lua session")
 old=sorted(folder.glob(f"horizontal_v1_6_1_{sid}_????.txt"))
 active=None
 for i,path in enumerate(old,1):
  if path.name!=f"horizontal_v1_6_1_{sid}_{i:04d}.txt":raise ValueError("Gap in sequence")
  match=re.fullmatch(r"SESSION:"+re.escape(sid)+r"\nLABEL:([A-Z0-9_]+)\n",path.read_text(encoding="ascii"))
  if not match or match.group(1) not in LABELS:raise ValueError("Malformed command")
  prev=match.group(1)
  if prev=="STOP":raise ValueError("Already stopped")
  phase,action=prev.split("_",1)
  if phase=="BEGIN" and active is None:active=action
  elif phase=="END" and active==action:active=None
  else:raise ValueError("Invalid previous bracket")
 if label=="STOP":
  if active is not None:raise ValueError("Close current action first")
 else:
  phase,action=label.split("_",1)
  if (phase=="BEGIN" and active is not None) or (phase=="END" and active!=action):
   raise ValueError("Bracket violation, active="+str(active))
 dest=folder/f"horizontal_v1_6_1_{sid}_{len(old)+1:04d}.txt"
 temp=dest.with_suffix(".txt.pending")
 try:
  with temp.open("x",encoding="ascii",newline="\n") as f:
   f.write(f"SESSION:{sid}\nLABEL:{label}\n");f.flush();os.fsync(f.fileno())
  if dest.exists():raise FileExistsError(dest)
  os.replace(temp,dest)
 finally:temp.unlink(missing_ok=True)
 return dest
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=sorted(LABELS));a=p.parse_args()
 print("Request created:",send(a.label).name)
 print("Wait for Lua marked confirmation BEFORE intervention or END.")
