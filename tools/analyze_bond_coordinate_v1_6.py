"""Read-only coordinate-v1.6 per-session audit; no global-axis inference."""
import csv
import json
import sys
from pathlib import Path

EC = "0x0D33EC"
F4 = "0x0D33F4"
OFFSETS = {EC, F4, "0x0D33E8", "0x0D33F0"}
GAPS = (1, 30, 120)

def analyze(sid, root=Path("output/csv")):
    if not sid or any(x in sid for x in "/\\\r\n"):
        raise ValueError("Invalid session")
    stem = root / ("bond_position_v1_3_" + sid)
    def load(suffix):
        with Path(str(stem) + suffix).open(encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))
    timeline = load("_timeline.csv")
    markers = load("_markers.csv")
    termination = load("_termination.csv")
    discontinuities = load("_discontinuities.csv")
    frames = {}
    for row in timeline:
        if row["session"] != sid:
            raise ValueError("Session mismatch")
        n = int(row["frame"])
        key = row["offset_hex"]
        if key in frames.setdefault(n, {}):
            raise ValueError("Duplicate offset/frame")
        frames[n][key] = row
    if not frames or any(set(fr) != OFFSETS for fr in frames.values()):
        raise ValueError("Missing or invalid timeline frame")
    order = [(int(x["frame"]), x["label"]) for x in markers]
    target_labels = [(f, l) for f, l in order if l in ("TARGET_EC", "TARGET_F4")]
    target = (EC if target_labels[0][1] == "TARGET_EC" else F4) if len(target_labels) == 1 else None
    other = F4 if target == EC else EC if target == F4 else None
    pre = next((f for f, l in order if l == "WRITE_PRE"), None)
    applied = next((f for f, l in order if l == "WRITE_APPLIED"), None)
    valid_order = [l for _, l in order] == [
        "TARGET_EC" if target == EC else "TARGET_F4", "BASELINE",
        "WRITE_PRE", "WRITE_APPLIED", "WRITE_OBSERVE", "STOP"] if target else False
    changes = []
    if target and pre is not None and applied is not None and pre < applied:
        for n in sorted(frames):
            if not pre < n <= applied or n-1 not in frames:
                continue
            before, after = frames[n-1][target], frames[n][target]
            if before["kseg0_hex"] == after["kseg0_hex"]:
                continue
            control_rows = [frames[f][other]["kseg0_hex"] for f in sorted(frames) if pre <= f <= n+120]
            checkpoints = {}
            for gap in GAPS:
                sample = frames.get(n+gap, {}).get(target)
                checkpoints[str(gap)] = None if sample is None else {
                    "frame": n+gap,
                    "hex": sample["kseg0_hex"],
                    "same_as_after": sample["kseg0_hex"] == after["kseg0_hex"],
                    "alias_equal": sample["alias_equal"] == "1"}
            try:
                delta = float(after["float32_be"]) - float(before["float32_be"])
            except (ValueError, TypeError):
                delta = None
            changes.append({
                "frame": n, "before_hex": before["kseg0_hex"],
                "after_hex": after["kseg0_hex"], "float32_be_delta": delta,
                "non_target_hex": control_rows[0] if control_rows else None,
                "non_target_stable_through_plus_120": bool(control_rows) and n+120 in frames and len(set(control_rows)) == 1,
                "checkpoints": checkpoints})
    mismatch = sum(r["alias_equal"] != "1" for r in timeline)
    clean = bool(termination and termination[-1]["reason"] == "stop"
                 and not discontinuities and mismatch == 0 and valid_order)
    isolated = bool(clean and len(changes) == 1
                    and changes[0]["non_target_stable_through_plus_120"]
                    and all(s and s["same_as_after"] and s["alias_equal"]
                            for s in changes[0]["checkpoints"].values()))
    result = {
        "session": sid, "target": target, "frames": len(frames),
        "marker_order_valid": valid_order, "clean_stop": bool(termination and termination[-1]["reason"] == "stop"),
        "alias_mismatches": mismatch, "discontinuities": len(discontinuities),
        "candidate_changes": changes, "isolated_memory_effect": isolated,
        "heading_degrees": None, "world_displacement_vector": None,
        "coordinate_frame_classification": "unresolved_requires_independent_geometry",
        "canonical_axis_validated": False,
        "limitations": ["Only change-window audit; unrelated motion outside window not assessed",
                        "No measured heading or world geometry; do not infer global axes from screen direction",
                        "Manual RAM intervention and camera stability require operator record"] }
    output = Path(str(stem) + "_coordinate_v1_6.json")
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return output, result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m tools.analyze_bond_coordinate_v1_6 SESSION_ID")
    path, result = analyze(sys.argv[1])
    print("Audit:", path, "frames:", result["frames"],
          "changes:", len(result["candidate_changes"]),
          "isolated:", result["isolated_memory_effect"],
          "axes:", result["coordinate_frame_classification"])
