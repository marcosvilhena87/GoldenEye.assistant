"""Atomic bracketed marker sender for Spatial Position Confirmation v1.7.4."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIONS=("REST_BASELINE","MOVE_LEFT","REST_AFTER_LEFT","MOVE_RIGHT",
"REST_AFTER_RIGHT","MOVE_FORWARD","REST_AFTER_FORWARD","MOVE_BACK",
"REST_AFTER_BACK","ROTATE_ONLY","REST_AFTER_ROTATION")
LABELS={"STOP"}|{f"{phase}_{action}" for action in ACTIONS for phase in ("BEGIN","END")}
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Unknown label")
 sid=(root/"output/sessions/spatial_v1_7_4_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 stem="spatial_v1_7_4_"+sid
 term=root/"output/csv"/(stem+"_termination.csv")
 if term.exists() and len(term.read_text(encoding="utf-8").splitlines())>1:
  raise RuntimeError("Session terminated")
 folder=root/"output/commands"
 old=sorted(folder.glob(stem+"_????.txt"))
 active=None
 for i,path in enumerate(old,1):
  if path.name!=f"{stem}_{i:04d}.txt":raise ValueError("Command sequence gap")
  match=re.fullmatch("SESSION:"+re.escape(sid)+r"\nLABEL:([A-Z0-9_]+)\n",path.read_text(encoding="ascii"))
  if not match or match[1] not in LABELS:raise ValueError("Malformed command")
  previous=match[1]
  if previous=="STOP":raise ValueError("Session already stopped")
  phase,action=previous.split("_",1)
  if phase=="BEGIN" and active is None:active=action
  elif phase=="END" and active==action:active=None
  else:raise ValueError("Invalid previous bracket")
 if label=="STOP":
  if active is not None:raise ValueError("End active phase first")
 else:
  phase,action=label.split("_",1)
  if (phase=="BEGIN" and active is not None) or (phase=="END" and active!=action):
   raise ValueError("Bracket violation; active="+str(active))
 dest=folder/f"{stem}_{len(old)+1:04d}.txt"
 pending=dest.with_suffix(".txt.pending")
 try:
  with pending.open("x",encoding="ascii",newline="\n") as f:
   f.write(f"SESSION:{sid}\nLABEL:{label}\n");f.flush();os.fsync(f.fileno())
  if dest.exists():raise FileExistsError(dest)
  os.replace(pending,dest)
 finally:pending.unlink(missing_ok=True)
 return dest
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=sorted(LABELS))
 print("Request created:",send(p.parse_args().label).name)
 print("Wait for the Lua 'marked' confirmation before intervention or next marker.")
