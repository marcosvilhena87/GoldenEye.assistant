"""Send an immutable, session-scoped, numbered v1.1 snapshot request."""
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("A1", "A_STABLE", "B", "B_STABLE", "A2", "CONTROL_A")
if len(sys.argv) != 2 or sys.argv[1] not in LABELS:
    sys.exit("Usage: python tools/send_autoaim_mem_v1_1.py A1|A_STABLE|B|B_STABLE|A2|CONTROL_A")
label = sys.argv[1]
session_file = ROOT / "output/sessions/autoaim_mem_v1_1_session.txt"
if not session_file.exists():
    sys.exit("Start autoaim_memory_discovery_v1_1.lua first.")
session = session_file.read_text(encoding="utf-8").strip()
manifest = ROOT / "output/csv/autoaim_mem_v1_1_manifest.csv"
records = []
if manifest.exists():
    with manifest.open(newline="", encoding="utf-8") as f:
        records = [r for r in csv.DictReader(f) if r["session"] == session]
done = [r["label"] for r in records]
if done != list(LABELS[:len(done)]):
    sys.exit("Manifest has unexpected labels or duplicates; inspect before sending.")
if len(done) == len(LABELS):
    sys.exit("All captures are already complete.")
expected = LABELS[len(done)]
if label != expected:
    sys.exit(f"Out of order: expected {expected}, got {label}.")
request = ROOT / "output/commands" / f"autoaim_mem_v1_1_{session}_{len(done)+1:02d}.txt"
request.parent.mkdir(parents=True, exist_ok=True)
body = f"SESSION:{session}\nSNAPSHOT:{label}\n"
try:
    with request.open("x", encoding="utf-8", newline="\n") as f:
        f.write(body)
except FileExistsError:
    if request.read_text(encoding="utf-8") != body:
        sys.exit("Conflicting existing request; inspect manually.")
    print("Existing request preserved:", request.name)
else:
    print("Request created:", request.name)
print("Verify the BizHawk 'captured' message and manifest before next request.")
