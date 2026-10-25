"""v1.7 world-axis calibration from independently measured fixed-world vectors.

Reads existing v1.6 audits + operator-authored manifest; never reads/writes emulator RAM.
A screen-relative direction alone is NOT a world measurement.
"""
import argparse
import json
import math
from pathlib import Path

EC = "0x0D33EC"
F4 = "0x0D33F4"


def vector(row):
    item = row.get("world_displacement")
    if not isinstance(item, dict):
        return None
    x, y = item.get("east"), item.get("north")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) for v in (x, y)):
        return None
    magnitude = math.hypot(x, y)
    return (x, y, magnitude) if magnitude > 0 else None


def evaluate(manifest, root=Path("output/csv")):
    runs = manifest["runs"]
    seen = set()
    rows = []
    for run in runs:
        sid = run["session"]
        if sid in seen or not sid or "/" in sid or "\\" in sid or ".." in sid:
            raise ValueError("Repeated or unsafe session ID")
        seen.add(sid)
        path = root / ("bond_position_v1_3_" + sid + "_coordinate_v1_6.json")
        audit = json.loads(path.read_text(encoding="utf-8"))
        target = audit.get("target")
        changes = audit.get("candidate_changes", [])
        ok = bool(audit.get("isolated_memory_effect") and len(changes) == 1 and
                  target == run["target"] and target in (EC, F4))
        delta = changes[0]["float32_be_delta"] if ok else None
        if ok and (not isinstance(delta, (int, float)) or not math.isfinite(delta) or delta == 0):
            ok = False
        heading = run.get("heading_degrees_clockwise")
        if isinstance(heading, bool) or not isinstance(heading, (int, float)) or not math.isfinite(heading):
            heading = None
        world = vector(run) if run.get("reference_type") == "independent_world_frame" else None
        quality = bool(run.get("same_world_start_confirmed") is True and
                       run.get("heading_independently_verified") is True and
                       run.get("camera_rotation_during_write") is False and
                       run.get("collision_or_snap") is False and
                       run.get("landmark_or_map_method") and world and heading is not None)
        ux, uy = (world[0]/world[2], world[1]/world[2]) if world else (None, None)
        rows.append({
            "session": sid, "target": target, "heading_deg_clockwise": heading,
            "signed_delta": delta, "isolated_memory_effect": ok,
            "world_vector": None if world is None else {"east":world[0],"north":world[1],"norm":world[2]},
            "normalized_world_direction_per_positive_delta": None if not (ok and world) else {
                "east": ux * (1 if delta > 0 else -1),
                "north": uy * (1 if delta > 0 else -1)},
            "eligible_world_reference": bool(ok and quality),
            "reason": "world geometry absent/unverified" if not quality else None,
            "screen_observation": run.get("screen_observation")
        })
    groups = {}
    for target in (EC, F4):
        group = [r for r in rows if r["target"] == target and r["eligible_world_reference"]]
        estimates = []
        for a in group:
            va = a["normalized_world_direction_per_positive_delta"]
            for b in group:
                if a["session"] >= b["session"]:
                    continue
                if abs((a["heading_deg_clockwise"]-b["heading_deg_clockwise"]+180)%360-180) < 45:
                    continue
                vb = b["normalized_world_direction_per_positive_delta"]
                dot = max(-1., min(1., va["east"]*vb["east"]+va["north"]*vb["north"]))
                estimates.append({"sessions":[a["session"],b["session"]],"angle_difference_deg":round(math.degrees(math.acos(dot)),3)})
        groups[target] = {"eligible_runs":len(group),"cross_heading_pairs":estimates,
                          "max_angle_difference_deg":max((v["angle_difference_deg"] for v in estimates), default=None)}
    # No automatic promotion: the threshold is an exploratory agreement diagnostic.
    enough = all(groups[t]["cross_heading_pairs"] for t in (EC,F4))
    agreement = enough and all(groups[t]["max_angle_difference_deg"] <= 15 for t in (EC,F4))
    result = {"protocol":"bond_world_axis_v1_7","runs":rows,"components":groups,
              "exploratory_fixed_world_alignment":bool(agreement),
              "calibration_status":"candidate_world_fixed_consistent_needs_independent_replication" if agreement
                    else "insufficient_or_inconsistent_independent_world_geometry",
              "x_z_labels_established":False,"canonical_symbol_promoted":False,
              "limitations":["World vectors must originate from independent static-world geometry, never screen arrows alone.",
                             "Heading and world coordinates are operator measurements, not extracted by this tool.",
                             "A <=15 degree agreement threshold is exploratory; it does not prove X/Z identity.",
                             "Different initial positions/collision/camera rotation disqualify comparison."]}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = evaluate(manifest)
    dest = args.output or args.manifest.with_name(args.manifest.stem + "_report.json")
    if dest.exists():
        raise FileExistsError(f"Will not overwrite: {dest}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("World-axis audit:", dest, "status:", report["calibration_status"],
          "eligible:", sum(x["eligible_world_reference"] for x in report["runs"]))


if __name__ == "__main__":
    main()
