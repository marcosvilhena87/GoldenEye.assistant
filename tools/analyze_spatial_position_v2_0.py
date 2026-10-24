"""Spatial Position Discovery v2.0: offline, raw-first audit of v1.9 telemetry.

No emulator access; no automatic validation of game coordinates.
"""
import argparse
import csv
import math
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

ADDRS = ("0x3B30D8", "0x3B30D0")
PHASES = ("BASELINE_HOLD", "FORWARD", "FORWARD_HOLD", "BACK",
          "BACK_HOLD", "ROTATE", "ROTATE_HOLD", "STRAFE", "STRAFE_HOLD")
FIELDS = ("session", "phase", "address", "frames", "first_frame", "last_frame",
          "first_raw", "last_raw", "unique_raw", "transitions",
          "transition_rate", "longest_constant_frames", "min_f32be",
          "max_f32be", "median_f32be", "range_f32be",
          "first_f32be", "last_f32be", "net_delta_f32be", "nonfinite_f32be")
EVENT_FIELDS = ("session", "frame", "phase", "address", "previous_raw",
                "raw_be", "previous_f32be", "f32be", "delta_f32be")
PAIR_FIELDS = ("session", "phase", "frames", "both_changed", "only_d8_changed",
               "only_d0_changed", "neither_changed", "either_changed",
               "synchrony_given_change")
RAW_FIELDS = ("session", "phase", "address", "raw_be", "count", "fraction")

def readcsv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def f32be(raw):
    return struct.unpack(">f", bytes.fromhex(raw))[0]

def validate(session, root):
    if not re.fullmatch(r"[A-Za-z0-9_]+", session):
        raise ValueError("Invalid session")
    folder = root / "output" / "csv"
    stem = "spatial_v1_9_" + session
    term = readcsv(folder / (stem + "_termination.csv"))
    if len(term) != 1 or term[0].get("reason") != "stop":
        raise ValueError("Completed STOP required")
    markers = readcsv(folder / (stem + "_markers.csv"))
    if [r["label"] for r in markers] != list(PHASES) + ["STOP"]:
        raise ValueError("Markers must be complete and ordered")
    marker_frames = [int(r["frame"]) for r in markers]
    if any(b <= a for a, b in zip(marker_frames, marker_frames[1:])):
        raise ValueError("Markers out of order")
    if readcsv(folder / (stem + "_discontinuities.csv")):
        raise ValueError("Frame discontinuity recorded")
    samples = readcsv(folder / (stem + "_samples.csv"))
    if not samples:
        raise ValueError("No samples")
    by_frame = defaultdict(dict)
    prev = -1
    for r in samples:
        if r.get("session") != session:
            raise ValueError("Mixed session")
        frame = int(r["frame"])
        if frame < prev:
            raise ValueError("Samples out of order")
        prev = frame
        addr, raw = r["address"], r["raw_be"]
        if addr not in ADDRS or not re.fullmatch(r"[0-9A-Fa-f]{8}", raw):
            raise ValueError("Bad address or raw value")
        phase = r["phase"]
        if frame < marker_frames[0]:
            expected = "PRESTART"
        elif frame >= marker_frames[-1]:
            raise ValueError("Unexpected sample after STOP")
        else:
            expected = PHASES[next(i for i in range(len(PHASES))
                                   if marker_frames[i] <= frame < marker_frames[i + 1])]
        if phase != expected:
            raise ValueError(f"Phase/frame mismatch at {frame}: {phase} != {expected}")
        if addr in by_frame[frame]:
            raise ValueError("Duplicate address per frame")
        by_frame[frame][addr] = raw.upper()
    if any(set(pair) != set(ADDRS) for pair in by_frame.values()):
        raise ValueError("Missing candidate reading in frame")
    frames = sorted(by_frame)
    if any(b != a + 1 for a, b in zip(frames, frames[1:])):
        raise ValueError("Missing frames in telemetry")
    if frames[0] > marker_frames[0] or frames[-1] < marker_frames[-1] - 1:
        raise ValueError("Missing phase coverage")
    return by_frame, marker_frames

def audit(session, by_frame, markers):
    frames = sorted(by_frame)
    phases = {}
    for frame in frames:
        if frame < markers[0]:
            continue  # PRESTART retained on disk, excluded from metrics
        phase = PHASES[next(i for i in range(len(PHASES))
                            if markers[i] <= frame < markers[i + 1])]
        phases.setdefault(phase, []).append(frame)
    stats, events, pairs, raws = [], [], [], []
    for phase in PHASES:
        pf = phases.get(phase, [])
        if not pf:
            raise ValueError("Empty experimental phase: " + phase)
        flags = defaultdict(dict)
        for addr in ADDRS:
            values = [by_frame[f][addr] for f in pf]
            floats = [f32be(raw) for raw in values]
            finite = [v for v in floats if math.isfinite(v)]
            counts = Counter(values)
            transitions = 0
            longest = current = 1
            for j in range(1, len(values)):
                changed = values[j] != values[j-1]
                flags[pf[j]][addr] = changed
                if changed:
                    transitions += 1
                    current = 1
                    old, new = floats[j-1], floats[j]
                    delta = new-old if math.isfinite(new) and math.isfinite(old) else ""
                    events.append(dict(session=session,frame=pf[j],phase=phase,
                                       address=addr,previous_raw=values[j-1],
                                       raw_be=values[j],previous_f32be=old,
                                       f32be=new,delta_f32be=delta))
                else:
                    current += 1
                longest = max(longest, current)
            fs = sorted(finite)
            median = ((fs[(len(fs)-1)//2] + fs[len(fs)//2])/2) if fs else ""
            stats.append(dict(session=session,phase=phase,address=addr,frames=len(pf),
                              first_frame=pf[0],last_frame=pf[-1],
                              first_raw=values[0],last_raw=values[-1],
                              unique_raw=len(counts),transitions=transitions,
                              transition_rate=transitions/max(1,len(pf)-1),
                              longest_constant_frames=longest,
                              min_f32be=fs[0] if fs else "",
                              max_f32be=fs[-1] if fs else "",
                              median_f32be=median,
                              range_f32be=fs[-1]-fs[0] if fs else "",
                              first_f32be=floats[0],last_f32be=floats[-1],
                              net_delta_f32be=floats[-1]-floats[0] if all(math.isfinite(x) for x in (floats[0],floats[-1])) else "",
                              nonfinite_f32be=len(floats)-len(finite)))
            for raw,count in counts.most_common():
                raws.append(dict(session=session,phase=phase,address=addr,
                                 raw_be=raw,count=count,fraction=count/len(values)))
        both=one_d8=one_d0=neither=0
        for f in pf[1:]:
            a=flags[f][ADDRS[0]]
            b=flags[f][ADDRS[1]]
            if a and b:both+=1
            elif a:one_d8+=1
            elif b:one_d0+=1
            else:neither+=1
        either=both+one_d8+one_d0
        pairs.append(dict(session=session,phase=phase,frames=len(pf)-1,
                          both_changed=both,only_d8_changed=one_d8,
                          only_d0_changed=one_d0,neither_changed=neither,
                          either_changed=either,
                          synchrony_given_change=both/either if either else ""))
    return stats,events,pairs,raws

def write(path, fields, rows):
    with path.open("x", encoding="utf-8", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def run(session,root):
    by_frame,markers=validate(session,root)
    results=audit(session,by_frame,markers)
    base=root/"output"/"csv"/("spatial_v2_0_"+session)
    suffixes=("_phase_summary.csv","_transitions.csv","_pair_sync.csv","_raw_frequencies.csv")
    fields=(FIELDS,EVENT_FIELDS,PAIR_FIELDS,RAW_FIELDS)
    paths=[Path(str(base)+s) for s in suffixes]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite previous v2.0 audit")
    for path,col,rows in zip(paths,fields,results):
        write(path,col,rows)
    return paths,results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    paths,results=run(a.session,a.root.resolve())
    for path,rows in zip(paths,results):
        print(f"Wrote {path} rows={len(rows)}")
    print("Read-only offline audit. Raw fields are hypotheses, not validated coordinates.")

if __name__=="__main__":
    main()
