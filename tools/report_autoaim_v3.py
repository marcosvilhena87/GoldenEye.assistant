"""Auto-aim v3 observational report, with session/epoch boundaries."""
from pathlib import Path
import csv,sys,collections
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"output/csv/autoaim_v3_events.csv"
if not p.exists():
    sys.exit("No events yet; run autoaim_mapping_v3.lua")
with p.open(encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f))
if not rows:
    sys.exit("Empty events CSV")
session=sys.argv[1] if len(sys.argv)>1 else rows[-1]["session"]
events=[r for r in rows if r["session"]==session]
if not events:
    sys.exit("Session not present")
groups=collections.defaultdict(list)
for r in events:
    groups[(int(r["epoch"]),r["phase"])].append(r)
print("SESSION",session)
print("Observed outcomes are operator reports, not independently verified auto-aim.")
for (epoch,phase),items in groups.items():
    outcomes=[r["detail"] for r in items if r["event"]=="OPERATOR"]
    intervention=[r["detail"] for r in items if r["event"]=="INTERVENTION_OPERATOR"]
    r_edges=sum(r["event"]=="RAW_R" and r["detail"]=="pressed" for r in items)
    z_edges=sum(r["event"]=="RAW_Z" and r["detail"]=="pressed" for r in items)
    print(f"epoch={epoch} phase={phase} frames={items[0]['frame']}..{items[-1]['frame']}"
          f" results={outcomes or '-'} interventions={intervention or '-'}"
          f" raw_R_presses={r_edges} raw_Z_presses={z_edges}")
print("A/B/A is observational until identical game state and settings are independently controlled.")
