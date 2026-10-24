"""Atomic operator phase commands for spatial v2.2 neighboring probe."""
import argparse,csv,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=("STILL","MOVE","HOLD","ROTATE","ROTATE_HOLD","STOP")
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Invalid label")
 sid=(root/"output/sessions/spatial_v2_2_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session ID")
 stem="spatial_v2_2_"+sid
 term=root/"output/csv"/(stem+"_termination.csv")
 if term.exists() and len(term.read_text(encoding="ascii").splitlines())>1:
  raise RuntimeError("Session terminated")
 folder=root/"output/commands"
 files=sorted(folder.glob(stem+"_????.txt"))
 if len(files)>=len(LABELS):raise ValueError("Session command sequence complete")
 markers=root/"output/csv"/(stem+"_markers.csv")
 with markers.open(encoding="ascii",newline="") as f:
  acknowledged={r["label"] for r in csv.DictReader(f)}
 for idx,path in enumerate(files):
  if path.name!=f"{stem}_{idx+1:04d}.txt":raise ValueError("Command numbering gap")
  if path.read_text(encoding="ascii")!=f"SESSION:{sid}\nLABEL:{LABELS[idx]}\n":
   raise ValueError("Invalid previous command")
  if LABELS[idx] not in acknowledged:raise RuntimeError("Await Lua 'marked "+LABELS[idx]+"'")
 if label!=LABELS[len(files)]:raise ValueError("Expected "+LABELS[len(files)])
 dest=folder/f"{stem}_{len(files)+1:04d}.txt"
 temp=dest.with_suffix(".txt.pending")
 try:
  with temp.open("x",encoding="ascii",newline="\n") as f:
   f.write(f"SESSION:{sid}\nLABEL:{label}\n");f.flush();os.fsync(f.fileno())
  if dest.exists():raise FileExistsError(dest)
  os.replace(temp,dest)
 finally:temp.unlink(missing_ok=True)
 return dest
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=LABELS)
 print("Request created:",send(p.parse_args().label).name)
 print("Wait for Lua 'marked' before moving or issuing the next command.")
