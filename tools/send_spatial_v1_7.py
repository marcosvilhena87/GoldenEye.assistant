"""Atomic spatial v1.7 snapshot queue. Creation != capture confirmation."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=("BOND_BASELINE","BOND_MOVE_LEFT","BOND_MOVE_RIGHT","BOND_MOVE_FORWARD",
"BOND_MOVE_BACK","BOND_ROTATE_LEFT","BOND_ROTATE_RIGHT","BOND_RETURN",
"SOLDIER_STATIONARY","SOLDIER_MOVED","ONE_GUARD_VISIBLE","NO_GUARD_VISIBLE",
"AUTOAIM_ON","AUTOAIM_OFF","STOP")
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Invalid label")
 sid=(root/"output/sessions/spatial_v1_7_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 stem="spatial_v1_7_"+sid
 term=root/"output/csv"/(stem+"_termination.csv")
 if term.exists() and len(term.read_text(encoding="ascii").splitlines())>1:raise RuntimeError("Session terminated")
 folder=root/"output/commands"
 prev=sorted(folder.glob(stem+"_????.txt"))
 for index,path in enumerate(prev,1):
  if path.name!=f"{stem}_{index:04d}.txt":raise ValueError("Command sequence gap")
  match=re.fullmatch("SESSION:"+re.escape(sid)+r"\nLABEL:([A-Z0-9_]+)\n",path.read_text(encoding="ascii"))
  if not match or match[1] not in LABELS:raise ValueError("Malformed command")
  if match[1]=="STOP":raise ValueError("Already stopped")
 dest=folder/f"{stem}_{len(prev)+1:04d}.txt"
 temp=dest.with_suffix(".txt.pending")
 try:
  with temp.open("x",encoding="ascii",newline="\n") as f:
   f.write(f"SESSION:{sid}\nLABEL:{label}\n")
   f.flush();os.fsync(f.fileno())
  if dest.exists():raise FileExistsError(dest)
  os.replace(temp,dest)
 finally:temp.unlink(missing_ok=True)
 return dest
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=LABELS)
 print("Request created:",send(p.parse_args().label).name)
 print("Wait for Lua captured confirmation BEFORE the next action.")
