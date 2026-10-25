"""Bond v1.5 read-only second-axis independence audit over v1.3 captures."""
import csv
import json
import sys
from pathlib import Path

EC = "0x0D33EC"
F4 = "0x0D33F4"
OFFSETS = {EC, F4, "0x0D33E8", "0x0D33F0"}
CHECKPOINTS = (1, 30, 120)


def audit(sid, root=Path("output/csv")):
    if not sid or any(c in sid for c in "/\\\r\n"):
        raise ValueError("Invalid session")
    stem = root / ("bond_position_v1_3_" + sid)

    def load(suffix):
        with Path(str(stem) + suffix).open(encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))

    timeline = load("_timeline.csv")
    markers = load("_markers.csv")
    term = load("_termination.csv")
    disc = load("_discontinuities.csv")
    if not timeline or len(timeline) % 4:
        raise ValueError("Missing/incomplete timeline")
    frames = {}
    for r in timeline:
        if r["session"] != sid:
            raise ValueError("Session mismatch")
        f = int(r["frame"])
        off = r["offset_hex"]
        if off in frames.setdefault(f, {}):
            raise ValueError(f"Duplicate {f}:{off}")
        frames[f][off] = r
    if any(set(x) != OFFSETS for x in frames.values()):
        raise ValueError("Missing tracked offsets")
    aliases = sum(r["alias_equal"] != "1" for r in timeline)
    entries = [(int(m["frame"]), m["label"]) for m in markers]
    required = ("TARGET_F4", "BASELINE", "WRITE_PRE", "WRITE_APPLIED", "WRITE_OBSERVE", "STOP")
    labels = [x[1] for x in entries]
    ordered = labels == list(required)
    pre = next((f for f, l in entries if l == "WRITE_PRE"), None)
    applied = next((f for f, l in entries if l == "WRITE_APPLIED"), None)
    observe = next((f for f, l in entries if l == "WRITE_OBSERVE"), None)
    stops = bool(term) and term[-1]["reason"] == "stop"
    candidates = []
    if pre is not None and applied is not None and pre < applied:
        for f in sorted(frames):
            if f <= pre or f > applied:
                continue
            prior = frames.get(f - 1)
            cur = frames[f]
            if prior is None:
                continue
            if cur[F4]["kseg0_hex"] == prior[F4]["kseg0_hex"]:
                continue
            cps = {}
            for gap in CHECKPOINTS:
                row = frames.get(f + gap, {}).get(F4)
                cps[str(gap)] = None if row is None else {
                    "frame": f + gap,
                    "hex": row["kseg0_hex"],
                    "same_as_after": row["kseg0_hex"] == cur[F4]["kseg0_hex"],
                    "alias_equal": row["alias_equal"] == "1",
                }
            segment = [frames[k] for k in sorted(frames) if pre <= k <= min(f + 120, max(frames))]
            ec_stable = len({x[EC]["kseg0_hex"] for x in segment}) == 1
            candidates.append({
                "change_frame": f,
                "f4_before": prior[F4]["kseg0_hex"],
                "f4_after": cur[F4]["kseg0_hex"],
                "f4_delta_float32_be": _delta(prior[F4]["float32_be"], cur[F4]["float32_be"]),
                "ec_baseline": segment[0][EC]["kseg0_hex"],
                "ec_stable_through_change_plus_120": ec_stable and f + 120 in frames,
                "checkpoints_from_actual_change": cps,
            })
    clean = bool(stops and not disc and aliases == 0 and ordered)
    independent = bool(clean and len(candidates) == 1 and candidates[0]["ec_stable_through_change_plus_120"]
                       and all(v and v["same_as_after"] and v["alias_equal"]
                               for v in candidates[0]["checkpoints_from_actual_change"].values()))
    result = {
        "session": sid,
        "target": F4,
        "frames": len(frames),
        "alias_mismatches": aliases,
        "clean_stop": stops,
        "discontinuities": len(disc),
        "required_marker_order": list(required),
        "actual_marker_order": labels,
        "marker_order_valid": ordered,
        "write_pre_frame": pre,
        "write_applied_frame": applied,
        "write_observe_frame": observe,
        "f4_change_candidates_in_intervention_window": candidates,
        "isolated_f4_memory_change_with_stable_ec": independent,
        "physical_lateral_movement_validated": False,
        "canonical_axis_validated": False,
        "limitations": [
            "An F4 transition is not automatically evidence that a manual write caused it",
            "The operator must report physical movement and camera/landmark observations separately",
            "Coordinates must not be named world X or Z from this memory audit alone",
            "An incomplete marker sequence or multiple F4 changes requires manual inspection",
        ],
    }
    out = Path(str(stem) + "_second_axis_v1_5.json")
    if out.exists():
        raise FileExistsError(f"Audit exists; will not overwrite: {out}")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out, result


def _delta(a, b):
    try:
        return float(b) - float(a)
    except (ValueError, TypeError, OverflowError):
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m tools.analyze_bond_second_axis_v1_5 SESSION_ID")
    p, r = audit(sys.argv[1])
    print("Audit:", p, "frames:", r["frames"],
          "F4 changes:", len(r["f4_change_candidates_in_intervention_window"]),
          "aliases:", r["alias_mismatches"],
          "isolated memory effect:", r["isolated_f4_memory_change_with_stable_ec"])
