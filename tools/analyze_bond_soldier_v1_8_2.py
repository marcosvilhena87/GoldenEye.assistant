"""Bond–Soldier correlation v1.8.2: offline diagnostics; no position claims or memory writes."""
import argparse
import csv
import json
import math
from pathlib import Path

EXPECTED = {"bond_e8", "bond_ec", "bond_f0", "bond_f4", "soldier_1_a", "soldier_1_b"}
SOLDIER = ("soldier_1_a", "soldier_1_b")
BOND = ("bond_ec", "bond_f4")
CONTROLS = {"BASELINE", "CAMERA_ONLY", "FREEZE_ON"}
def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def analyze(sid, root=Path("output/csv")):
    if not sid or "/" in sid or "\\" in sid or ".." in sid:
        raise ValueError("unsafe session")
    stem = root / ("bond_soldier_v1_8_2_" + sid)
    timeline = read_csv(Path(str(stem) + "_timeline.csv"))
    markers = read_csv(Path(str(stem) + "_markers.csv"))
    termination = read_csv(Path(str(stem) + "_termination.csv"))
    if not timeline:
        raise ValueError("empty timeline")
    frames = {}
    alias_mismatches = []
    for r in timeline:
        if r["session"] != sid or r["field"] not in EXPECTED:
            raise ValueError("unexpected session or field")
        n = int(r["frame"])
        if r["field"] in frames.setdefault(n, {}):
            raise ValueError("duplicate field")
        frames[n][r["field"]] = r
        if r["alias_equal"] != "1":
            alias_mismatches.append({"frame": n, "field": r["field"]})
    seq_all = sorted(frames)
    incomplete = [{"frame": n, "missing_fields": sorted(EXPECTED - set(frames[n]))}
                  for n in seq_all if set(frames[n]) != EXPECTED]
    # A live logger flushes the timeline every 30 frames. A reader can see
    # the newest frame halfway through its six records. Never treat it as valid.
    # Interior incomplete frames are not safe to bridge or silently discard.
    if any(item["frame"] != seq_all[-1] for item in incomplete):
        raise ValueError("incomplete interior six-field frames: " + str(incomplete[:10]))
    if incomplete:
        frames.pop(seq_all[-1])
    seq = sorted(frames)
    if not seq:
        raise ValueError("no complete six-field frames")
    gaps = [{"before": a, "after": b} for a, b in zip(seq, seq[1:]) if b != a + 1]
    changes = []
    for a, b in zip(seq, seq[1:]):
        if b != a + 1:
            continue
        for field in sorted(EXPECTED):
            old, new = frames[a][field], frames[b][field]
            if old["kseg0_hex"] != new["kseg0_hex"]:
                try:
                    delta = float(new["float32_be"]) - float(old["float32_be"])
                    if not math.isfinite(delta):
                        delta = None
                except (ValueError, TypeError):
                    delta = None
                changes.append({"frame": b, "field": field,
                                "before_hex": old["kseg0_hex"], "after_hex": new["kseg0_hex"],
                                "delta_float32": delta, "phase": new["phase"]})
    phases = {}
    for n in seq:
        phases.setdefault(frames[n]["bond_ec"]["phase"], []).append(n)
    phase_stats = []
    for phase, nums in phases.items():
        for field in sorted(EXPECTED):
            vals = [frames[n][field]["kseg0_hex"] for n in nums]
            phase_stats.append({"phase": phase, "field": field, "frames": len(nums),
                                "distinct_raw_values": len(set(vals)),
                                "stable_raw": len(set(vals)) == 1})
    def soldier_stable(a, b):
        return all(frames[a][f]["kseg0_hex"] == frames[b][f]["kseg0_hex"] for f in SOLDIER)
    interventions = []
    for c in changes:
        if c["field"] not in BOND:
            continue
        frame = c["frame"]
        if frame-1 not in frames:
            continue
        post = [n for n in seq if frame <= n <= frame+120]
        available = bool(post) and len(post) == 121 and all(
            b == a+1 for a,b in zip(post,post[1:]))
        interventions.append({"frame": frame, "bond_field": c["field"],
                              "delta_float32": c["delta_float32"],
                              "soldier_unchanged_at_transition": soldier_stable(frame-1, frame),
                              "soldier_stable_next_120_frames": (
                                all(soldier_stable(frame, n) for n in post) if available else None),
                              "window_120_complete": available})
    markers_sorted = [{"frame": int(m["frame"]), "label": m["label"]} for m in markers]
    report = {
        "protocol": "bond_soldier_coordinate_correlation_v1_8_2",
        "session": sid, "frames": len(seq), "incomplete_frames": incomplete,
        "capture_complete": not incomplete and bool(termination and termination[-1].get("reason") == "stop"),
        "changes": changes,
        "intervention_candidates": interventions, "phase_stats": phase_stats,
        "markers": markers_sorted, "alias_mismatches": alias_mismatches,
        "timeline_gaps": gaps, "termination": termination,
        "clean_stop": bool(termination and termination[-1].get("reason") == "stop"),
        "soldier_field_interpretation_validated": False,
        "physical_position_correlation_validated": False,
        "canonical_axes_validated": False,
        "notes": [
            "Coincident stable memory fields do not prove world-space coordinates.",
            "Two soldier fields may be unrelated to EC/F4 or each other.",
            "Changes are detected from raw bytes, independently of WRITE_APPLIED timing.",
            "Frozen AI and stable bytes do not establish physical soldier stationarity.",
            "Only independently validated same-frame geometry can support a spatial claim.",
            "An incomplete final frame is excluded and capture_complete is false; stop the Lua logger before final audit."
        ]}
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root", type=Path, default=Path("output/csv"))
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    report = analyze(a.session, a.root)
    path = a.output or a.root / ("bond_soldier_v1_8_2_" + a.session + "_analysis.json")
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Correlation:", path, "frames:", report["frames"], "changes:", len(report["changes"]),
          "aliases:", len(report["alias_mismatches"]), "stop:", report["clean_stop"])

if __name__ == "__main__":
    main()
