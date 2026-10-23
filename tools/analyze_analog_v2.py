"""Summarize analog raw input by phase without asserting game deadzone."""
from pathlib import Path
import csv
from collections import defaultdict

p=Path(__file__).resolve().parents[1]/"output/csv/analog_v2_samples.csv"
if not p.exists():
    raise SystemExit(f"Missing {p} (run analog_mapping_v2.lua first)")
rows=list(csv.DictReader(p.open(newline="",encoding="utf-8")))
if not rows:
    raise SystemExit("No samples")
session=rows[-1]["session"]
phases=defaultdict(list)
for r in rows:
    if r["session"]==session and r["kind"]!="PHASE_SNAPSHOT":
        phases[r["phase"]].append((int(float(r["frame"])),float(r["x_axis"]),float(r["y_axis"])))
print("Session:",session)
print("PHASE                N     X MIN/MAX         Y MIN/MAX      FIRST NONZERO")
for phase,values in phases.items():
    xs=[v[1] for v in values];ys=[v[2] for v in values]
    active=next((v for v in values if v[1] or v[2]),None)
    first=str(active[0]) if active else "-"
    print(f"{phase:20s} {len(values):5d} {min(xs):6.1f}/{max(xs):6.1f} {min(ys):8.1f}/{max(ys):6.1f} {first:>12s}")
print("WARNING: minimum nonzero API input is not the in-game deadzone threshold.")
