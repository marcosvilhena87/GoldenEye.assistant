"""Strict, atomic v1.9 phase marker sender. Marked != physical movement verified."""
import argparse,csv,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=("BASELINE_HOLD","FORWARD","FORWARD_HOLD","BACK","BACK_HOLD","ROTATE","ROTATE_HOLD","STRAFE","STRAFE_HOLD","STOP")
def send(label,root=ROOT):
 if label not in LABELS:raise ValueError("Invalid label")
 sid=(root/"output/sessions/spatial_v1_9_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid session")
 stem="spatial_v1_9_"+sid
 term=root/"output/csv"/(stem+"_termination.csv")
 if term.exists() and len(term.read_text(encoding="ascii").splitlines())>1:raise RuntimeError("Session already finished")
 folder=root/"output/commands"
 existing=sorted(folder.glob(stem+"_????.txt"))
 if len(existing)>=len(LABELS):raise ValueError("All markers already queued")
 for idx,p in enumerate(existing):
  if p.name!=f"{stem}_{idx+1:04d}.txt":raise ValueError("Gap in command queue")
  body=p.read_text(encoding="ascii")
  if body!=f"SESSION:{sid}\nLABEL:{LABELS[idx]}\n":raise ValueError("Malformed or out-of-order command")
  marks=root/"output/csv"/(stem+"_markers.csv")
  with marks.open(newline="",encoding="ascii") as f: acknowledged={row["label"] for row in csv.DictReader(f)}
  if LABELS[idx] not in acknowledged:raise RuntimeError("Wait for Lua marked "+LABELS[idx])
 if label!=LABELS[len(existing)]:raise ValueError("Expected "+LABELS[len(existing)])
 dest=folder/f"{stem}_{len(existing)+1:04d}.txt"
 tmp=dest.with_suffix(".txt.pending")
 try:
  with tmp.open("x",encoding="ascii",newline="\n") as f:
   f.write(f"SESSION:{sid}\nLABEL:{label}\n");f.flush();os.fsync(f.fileno())
  if dest.exists():raise FileExistsError(dest)
  os.replace(tmp,dest)
 finally:tmp.unlink(missing_ok=True)
 return dest
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=LABELS)
 print("Request created:",send(p.parse_args().label).name)
 print("Wait for Lua 'marked' before next phase; input movements are manual.")
