"""Atomic, immutable capture requests for v1.2.1. Never edits historical v1.2 data."""
from pathlib import Path
import csv
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
LABELS = ("ON1", "ON_STABLE", "OFF1", "OFF_STABLE", "ON2",
          "MENU_NO_CHANGE", "OFF2", "ON3")

def next_request(label, root=OUT):
    if label not in LABELS:
        raise ValueError("Unknown label: " + label)
    sid_file = root / "sessions" / "autoaim_mem_v1_2_1_session.txt"
    if not sid_file.is_file():
        raise RuntimeError("Start the v1.2.1 collector first")
    session = sid_file.read_text(encoding="ascii").strip()
    if not session or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_" for c in session):
        raise RuntimeError("Invalid session identifier")
    manifest = root / "csv" / ("autoaim_mem_v1_2_1_manifest_" + session + ".csv")
    completed = []
    if manifest.exists():
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if any(r.get("session") != session or r.get("count") != "131" for r in rows):
            raise RuntimeError("Manifest integrity check failed")
        completed = [r["label"] for r in rows]
    if completed != list(LABELS[:len(completed)]):
        raise RuntimeError("Manifest sequence invalid; stop")
    if len(completed) == len(LABELS):
        raise RuntimeError("Session complete")
    expected = LABELS[len(completed)]
    if label != expected:
        raise RuntimeError("Expected " + expected)
    dest = root / "commands" / ("autoaim_mem_v1_2_1_" + session + "_%02d.txt" % (len(completed)+1))
    body = "SESSION:" + session + "\nSNAPSHOT:" + expected + "\n"
    if dest.exists():
        if dest.read_text(encoding="ascii") != body:
            raise RuntimeError("Conflicting existing command")
        return "Request already exists: " + dest.name
    # Exclusive temp creation, same directory/volume, then atomic visibility.
    temp = dest.with_suffix(".txt.pending")
    try:
        with temp.open("x", encoding="ascii", newline="\n") as out:
            out.write(body)
            out.flush()
            os.fsync(out.fileno())
        if dest.exists():
            raise RuntimeError("Command appeared concurrently; stop")
        os.replace(temp, dest)
    finally:
        if temp.exists():
            temp.unlink()
    return "Request created: " + dest.name

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python tools/send_autoaim_mem_v1_2_1.py LABEL")
    try:
        print(next_request(sys.argv[1]))
        print("Confirm captured message AND session manifest before next command.")
    except (OSError, ValueError, RuntimeError) as exc:
        sys.exit("ERROR: " + str(exc))
