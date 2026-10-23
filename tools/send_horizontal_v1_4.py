"""Atomic, bracketed v1.4 marker sender; confirms creation, NOT Lua consumption."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIONS=("BASELINE","ON_TARGET_LEFT","ON_TARGET_RIGHT","ON_TARGET_CENTER","OFF_TARGET_LEFT","OFF_TARGET_RIGHT","NO_TARGET","TURN_CAMERA_CONTROL")
LABELS={"STOP"}|{f"{p}_{a}" for a in ACTIONS for p in ("BEGIN","END")}
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Unknown label")
 sid=(root/"output/sessions/horizontal_v1_4_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 folder=root/"output/commands"
 old=sorted(folder.glob(f"horizontal_v1_4_{sid}_????.txt"))
 active=None
 for i,path in enumerate(old,1):
  if path.name!=f"horizontal_v1_4_{sid}_{i:04d}.txt":raise ValueError("Gap in sequence")
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
 dest=folder/f"horizontal_v1_4_{sid}_{len(old)+1:04d}.txt"
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
