"""Dual-axis same-frame candidate distance from v1.8.8.1 temporal RDRAM CSV.

Values/axes are hypotheses. No physical 2D distance or entity ID is validated.
"""
import argparse
import csv
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

CONFIGS = {
    "historical": ((0x06D248, 0x06D250), (0x20F594, 0x20F5AC)),
    "alternate": ((0x06D248, 0x06D250), (0x20F578, 0x20F580)),
    "duplicate_region": ((0x06D248, 0x06D250), (0x06A120, 0x06A128)),
    "bond_alias_historical": ((0x0D33EC, 0x0D33F4), (0x20F594, 0x20F5AC)),
}
PHASES = ("BASELINE", "BOND_APPROACH", "SOLDIER_CHASE", "BOND_RETREAT",
          "SOLDIER_REPOSITION", "FREEZE_REQUEST_ON", "FREEZE_CONFIRMED")
MAX_ABS_VALUE = 1e8


def _decode(raw):
    if len(raw) != 8:
        return None
    try:
        value = struct.unpack(">f", bytes.fromhex(raw))[0]
    except (ValueError, struct.error):
        return None
    return value if math.isfinite(value) and abs(value) < MAX_ABS_VALUE else None


def _metrics(samples):
    if not samples:
        return None
    initial, final = samples[0], samples[-1]
    minimum = min(samples, key=lambda x: x["distance"])
    return {
        "frames": len(samples),
        "start_frame": initial["frame"], "end_frame": final["frame"],
        "first_distance": initial["distance"],
        "last_distance": final["distance"],
        "delta_distance": final["distance"] - initial["distance"],
        "minimum_distance": minimum["distance"],
        "minimum_frame": minimum["frame"],
        "components_at_minimum": {"axis_a": minimum["delta_a"], "axis_b": minimum["delta_b"]},
        "first_components": {"axis_a": initial["delta_a"], "axis_b": initial["delta_b"]},
        "last_components": {"axis_a": final["delta_a"], "axis_b": final["delta_b"]},
    }


def analyze(sid, root=Path("output/csv"), min_frames=30):
    if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):
        raise ValueError("invalid session")
    if min_frames < 2:
        raise ValueError("min_frames must be >=2")
    path = Path(root) / f"soldier_chase_v1_8_8_1_{sid}_timeline.csv"
    frames, phases = defaultdict(dict), {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["session"] != sid:
                raise ValueError("mixed session")
            frame, offset = int(row["frame"]), int(row["offset_hex"], 16)
            if offset in frames[frame]:
                raise ValueError("duplicate frame / offset")
            frames[frame][offset] = row["raw_be"]
            if frame in phases and phases[frame] != row["phase"]:
                raise ValueError("mixed phase within frame")
            phases[frame] = row["phase"]
    if not frames:
        raise ValueError("empty timeline")
    ordered_frames = sorted(frames)
    discontinuities = [[a, b] for a, b in zip(ordered_frames, ordered_frames[1:]) if b != a + 1]
    outputs = []
    for name, (bond, soldier) in CONFIGS.items():
        required = (*bond, *soldier)
        by_phase = defaultdict(list)
        invalid = 0
        for frame in ordered_frames:
            values = [(_decode(frames[frame][o]) if o in frames[frame] else None) for o in required]
            if any(v is None for v in values):
                invalid += 1
                continue
            ba, bb, sa, sb = values
            da, db = sa - ba, sb - bb
            dist = math.hypot(da, db)
            if not math.isfinite(dist):
                invalid += 1
                continue
            by_phase[phases[frame]].append({
                "frame": frame, "distance": dist, "delta_a": da, "delta_b": db
            })
        metrics = {phase: _metrics(by_phase[phase]) if len(by_phase[phase]) >= min_frames else None
                   for phase in PHASES}
        approach = metrics["BOND_APPROACH"]
        retreat = metrics["BOND_RETREAT"]
        outputs.append({
            "name": name,
            "bond_offsets": [f"0x{o:06X}" for o in bond],
            "soldier_offsets": [f"0x{o:06X}" for o in soldier],
            "decode": "float32_big_endian",
            "invalid_or_missing_frames": invalid,
            "phase_metrics": metrics,
            "approach_converged": bool(approach and approach["delta_distance"] < 0),
            "retreat_diverged": bool(retreat and retreat["delta_distance"] > 0),
            "both_phases_available": bool(approach and retreat),
            "distance_units": "hypothetical_common_numeric_units",
            "interpretation": "hypothesis_only",
        })
    return {
        "protocol": "soldier_dual_axis_distance_v1_8_9",
        "session": sid,
        "frames": len(ordered_frames),
        "timeline_gaps": discontinuities,
        "phase_min_frames": min_frames,
        "configs": outputs,
        "distance_is_physical_validated": False,
        "bond_axes_validated": False,
        "soldier_axes_validated": False,
        "soldier_identity_validated": False,
        "cross_save_validated": False,
        "limitations": [
            "A and B are hypothetical float32 big-endian axes, not validated X/Z.",
            "Same-frame data still originates from sequential reads of RAM.",
            "An end-to-end phase decrease may occur without monotonically decreasing physical distance.",
            "The soldier may move while Bond approaches or retreats.",
            "Same-frame 2D candidate distance cannot establish the entity's RAM identity.",
            "Another save and independent spatial observation are required.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session")
    parser.add_argument("--root", type=Path, default=Path("output/csv"))
    parser.add_argument("--min-frames", type=int, default=30)
    args = parser.parse_args()
    report = analyze(args.session, args.root, args.min_frames)
    dest = args.root / f"soldier_dual_axis_v1_8_9_{args.session}_analysis.json"
    if dest.exists():
        raise FileExistsError(dest)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Dual Axis v1.8.9:", dest, "frames:", report["frames"],
          "configs:", len(report["configs"]))


if __name__ == "__main__":
    main()
