"""Atomic sequential capture requests for horizontal correction exploration."""
import argparse,csv,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=("ON_NO_TARGET","ON_LEFT","ON_CENTER","ON_RIGHT","OFF_LEFT","OFF_CENTER","OFF_RIGHT","ON_LEFT_REPEAT")
def send(label,root=ROOT):
 sid=(root/"output/sessions/horizontal_v1_session.txt").read_text(encoding="ascii").strip()
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Bad session")
 path=root/"output/csv"/f"horizontal_v1_manifest_{sid}.csv"
 with path.open(newline="",encoding="utf-8") as f:records=list(csv.DictReader(f))
 if any(r["session"]!=sid or r["domain"]!="RDRAM" or int(r["size"])!=8388608 for r in records):
  raise ValueError("Invalid manifest")
 if [r["label"] for r in records]!=list(LABELS[:len(records)]):raise ValueError("Bad capture sequence")
 if len(records)>=len(LABELS):raise ValueError("Complete")
 expected=LABELS[len(records)]
 if label!=expected:raise ValueError("Expected "+expected)
 destination=root/"output/commands"/f"horizontal_v1_{sid}_{len(records)+1:02d}.txt"
 body=f"SESSION:{sid}\nSNAPSHOT:{label}\n"
 if destination.exists():
  if destination.read_text(encoding="ascii")!=body:raise ValueError("Conflicting request")
  return destination
 pending=destination.with_suffix(".txt.pending")
 try:
  with pending.open("x",encoding="ascii",newline="\n") as f:
   f.write(body);f.flush();os.fsync(f.fileno())
  if destination.exists():raise FileExistsError(destination)
  os.replace(pending,destination)
 finally:pending.unlink(missing_ok=True)
 return destination
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("label",choices=LABELS);a=p.parse_args()
 print("Request:",send(a.label).name)
 print("Wait for BizHawk 'captured' and manifest confirmation before next request.")
