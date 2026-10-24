"""Atomic spatial v1.8 snapshot queue. Creation != capture confirmation."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=("BASELINE_STILL","LEFT_MID","LEFT_END","LEFT_HOLD","RIGHT_MID","RIGHT_END","RIGHT_HOLD","FORWARD_MID","FORWARD_END","FORWARD_HOLD","BACK_MID","BACK_END","BACK_HOLD","ROTATE_END","STOP")
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Invalid label")
 sid=(root/"output/sessions/spatial_v1_8_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 stem="spatial_v1_8_"+sid
 term=root/"output/csv"/(stem+"_termination.csv")
 if term.exists() and len(term.read_text(encoding="ascii").splitlines())>1:raise RuntimeError("Session terminated")
 folder=root/"output/commands"
 prev=sorted(folder.glob(stem+"_????.txt"))
 for index,path in enumerate(prev,1):
  if path.name!=f"{stem}_{index:04d}.txt":raise ValueError("Command sequence gap")
  match=re.fullmatch("SESSION:"+re.escape(sid)+r"\nLABEL:([A-Z0-9_]+)\n",path.read_text(encoding="ascii"))
  if not match or match[1] not in LABELS:raise ValueError("Malformed command")
  if match[1]=="STOP":raise ValueError("Already stopped")
  if match[1]!=LABELS[index-1]:raise ValueError("Prior commands are out of order")
 if label!=LABELS[len(prev)]:raise ValueError("Unexpected next label: "+label+"; expected "+LABELS[len(prev)])
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
