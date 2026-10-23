"""Queue one immutable v1.2 capture command; no mutation of game state."""
from pathlib import Path
import csv,sys
ROOT=Path(__file__).resolve().parents[1]
LABELS=("ON1","ON_STABLE","OFF1","OFF_STABLE","ON2","MENU_NO_CHANGE","OFF2","ON3")
if len(sys.argv)!=2 or sys.argv[1] not in LABELS:sys.exit("Usage: python tools/send_autoaim_mem_v1_2.py "+("|".join(LABELS)))
session_path=ROOT/"output/sessions/autoaim_mem_v1_2_session.txt"
if not session_path.is_file():sys.exit("Start the v1.2 collector first")
session=session_path.read_text().strip()
manifest=ROOT/"output/csv/autoaim_mem_v1_2_manifest.csv"
with manifest.open(newline="",encoding="utf-8") as f:
 rows=[r for r in csv.DictReader(f) if r["session"]==session]
if manifest.exists() else []
done=[r["label"] for r in rows]
if done!=list(LABELS[:len(done)]):sys.exit("Manifest contains unexpected labels; stop")
if len(done)>=len(LABELS):sys.exit("Session already complete")
expected=LABELS[len(done)]
if sys.argv[1]!=expected:sys.exit("Expected "+expected)
request=ROOT/"output/commands"/f"autoaim_mem_v1_2_{session}_{len(done)+1:02d}.txt"
body=f"SESSION:{session}\nSNAPSHOT:{expected}\n"
try:
 with request.open("x",encoding="ascii",newline="\n") as f:f.write(body)
 print("Request created:",request.name)
except FileExistsError:
 if request.read_text()!=body:sys.exit("Conflicting existing command")
 print("Request already exists:",request.name)
print("Confirm collector output and manifest; do not assume capture from this message.")
