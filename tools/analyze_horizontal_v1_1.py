#!/usr/bin/env python3
"""Horizontal Correction v1.1: offline typed reinterpretation of the eight v1 dumps.

No game writes, inferred addresses, symbol promotion or angular claims.
"""
import argparse
import csv
import math
import re
import struct
from pathlib import Path

try:
    from tools.analyze_horizontal_v1 import LABELS
except ModuleNotFoundError as exc:
    if exc.name != "tools":
        raise
    from analyze_horizontal_v1 import LABELS  # direct execution: python tools/script.py

EXPECTED_SIZE = 8388608
FORMATS = (("int16_be", ">h"), ("int16_le", "<h"),
           ("int32_be", ">i"), ("int32_le", "<i"),
           ("float32_be", ">f"), ("float32_le", "<f"))
FIELDS = ("offset_hex", "encoding", "width_bytes", "on_left", "on_center",
          "on_right", "off_left", "off_center", "off_right", "on_no_target",
          "on_left_repeat", "on_spatial_distinct", "off_spatial_constant",
          "repeat_exact", "on_off_left_differs", "finite_all",
          "monotonic_on", "evidence_status")


def candidate_locations(candidate_csv):
    with candidate_csv.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or "offset_hex" not in rows[0]:
        raise ValueError("Candidate CSV empty or missing offset_hex")
    found = set()
    for row in rows:
        raw = row["offset_hex"]
        if not re.fullmatch(r"0x[0-9A-Fa-f]{1,6}", raw or ""):
            raise ValueError("Invalid candidate offset: " + str(raw))
        offset = int(raw, 16)
        if offset >= EXPECTED_SIZE:
            raise ValueError("Candidate outside RDRAM")
        if offset in found:
            raise ValueError("Duplicate candidate offset")
        found.add(offset)
    # Do not assume candidates fall on type alignment; scan neighboring
    # type starts so a changed byte can be any byte of the stored number.
    return sorted({start for offset in found for start in range(max(0, offset - 3), offset + 1)
                   if start + 4 <= EXPECTED_SIZE})


def read_manifest(root, session):
    manifest = root / "csv" / ("horizontal_v1_manifest_" + session + ".csv")
    with manifest.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if (len(rows) != len(LABELS) or [r.get("label") for r in rows] != list(LABELS)
        or any(r.get("session") != session or r.get("domain") != "RDRAM"
               or int(r.get("size", 0)) != EXPECTED_SIZE for r in rows)):
        raise ValueError("Incomplete or inconsistent session manifest")
    return rows


def decode_values(samples, format_code):
    values = [struct.unpack(format_code, sample)[0] for sample in samples]
    if format_code.endswith("f") and not all(math.isfinite(v) for v in values):
        return None
    return values


def analyze_typed(data, starts):
    if set(data) != set(LABELS) or any(len(data[k]) != EXPECTED_SIZE for k in LABELS):
        raise ValueError("Missing, incomplete or extra snapshot")
    output = []
    for offset in starts:
        for name, fmt in FORMATS:
            width = struct.calcsize(fmt)
            if offset + width > EXPECTED_SIZE:
                continue
            samples = [data[label][offset:offset + width] for label in LABELS]
            values = decode_values(samples, fmt)
            if values is None:
                continue
            (no, left, center, right, off_left, off_center, off_right, repeat) = values
            distinct = len({left, center, right}) == 3
            constant = off_left == off_center == off_right
            replay = left == repeat
            differs = left != off_left
            monotonic = (left < center < right or left > center > right)
            if not (distinct and constant and replay):
                continue
            output.append(dict(
                offset_hex=f"0x{offset:06X}", encoding=name, width_bytes=width,
                on_left=left, on_center=center, on_right=right,
                off_left=off_left, off_center=off_center, off_right=off_right,
                on_no_target=no, on_left_repeat=repeat,
                on_spatial_distinct=True, off_spatial_constant=True,
                repeat_exact=True, on_off_left_differs=differs,
                finite_all=True, monotonic_on=monotonic,
                evidence_status="typed_candidate_only"))
    return output


def run(session, root):
    if not re.fullmatch(r"[A-Za-z0-9_]+", session):
        raise ValueError("Invalid session identifier")
    read_manifest(root, session)
    csvpath = root / "csv" / ("horizontal_v1_candidates_" + session + ".csv")
    starts = candidate_locations(csvpath)
    data = {}
    for label in LABELS:
        path = root / "archive" / f"horizontal_v1_{session}_{label}.bin"
        raw = path.read_bytes()
        if len(raw) != EXPECTED_SIZE:
            raise ValueError(f"Bad size: {path} ({len(raw)})")
        data[label] = raw
    rows = analyze_typed(data, starts)
    destination = root / "csv" / ("horizontal_v1_1_typed_candidates_" + session + ".csv")
    with destination.open("x", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return destination, len(starts), len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session")
    parser.add_argument("--directory", type=Path, default=Path("output"))
    args = parser.parse_args()
    dest, starts, count = run(args.session, args.directory)
    print("Wrote", dest)
    print("Candidate start offsets:", starts, "typed candidate interpretations:", count)
    print("Descriptive only: no proven horizontal correction, angles or validated symbols.")


if __name__ == "__main__":
    main()
