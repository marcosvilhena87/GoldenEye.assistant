"""v1.8 independent 2D landmark affine survey. Stdlib only; never reads RAM.

Inputs: 3+ noncollinear fixed landmarks observed in a map/survey image, each
paired with an independently surveyed local-world coordinate. Bond before/after
are marked in that SAME fixed map, not inferred from EC/F4 or FPS image shifts.
"""
import argparse
import json
import math
from pathlib import Path


def xy(obj, keys):
    if not isinstance(obj, dict):
        raise ValueError("Expected coordinate object")
    a, b = [obj.get(k) for k in keys]
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (a, b)):
        raise ValueError("Missing/nonfinite coordinate: " + str(keys))
    return (float(a), float(b))


def solve3(a, b):
    m = [list(map(float, r)) + [float(v)] for r, v in zip(a, b)]
    for i in range(3):
        pivot = max(range(i, 3), key=lambda j: abs(m[j][i]))
        if abs(m[pivot][i]) < 1e-10:
            raise ValueError("Landmarks do not span a measurable 2D frame")
        m[i], m[pivot] = m[pivot], m[i]
        scale = m[i][i]
        m[i] = [v / scale for v in m[i]]
        for j in range(3):
            if j != i:
                factor = m[j][i]
                m[j] = [x - factor*y for x, y in zip(m[j], m[i])]
    return [r[-1] for r in m]


def calibrate(data):
    if data.get("observation_source") != "independent_fixed_topdown_map":
        raise ValueError("Independent fixed top-down map required; FPS screenshots are insufficient")
    if data.get("bond_coordinates_derived_from_ec_f4") is not False:
        raise ValueError("Bond marks must not be derived from EC/F4")
    if data.get("fixed_map_and_scale_verified") is not True:
        raise ValueError("Map scale and frame must be independently verified")
    anchors = data.get("landmarks", [])
    if len(anchors) < 4:
        raise ValueError("At least 4 fixed landmarks required (3 geometry + 1+ residual checks)")
    pixels = [xy(v["pixel"], ("x", "y")) for v in anchors]
    world = [xy(v["world"], ("east", "north")) for v in anchors]
    rows = [[x, y, 1.] for x, y in pixels]
    normal = [[sum(r[i]*r[j] for r in rows) for j in range(3)] for i in range(3)]
    params = [solve3(normal, [sum(r[i]*w[axis] for r, w in zip(rows, world)) for i in range(3)]) for axis in range(2)]
    def transform(point):
        x, y = xy(point, ("x", "y"))
        return tuple(c[0]*x+c[1]*y+c[2] for c in params)
    residuals = []
    for a, w, p in zip(anchors, world, pixels):
        fitted = transform({"x":p[0],"y":p[1]})
        residuals.append({"id":a["id"],"error":round(math.dist(fitted,w),6)})
    rmse = math.sqrt(sum(x["error"]**2 for x in residuals)/len(residuals))
    max_allowed = data.get("max_anchor_rmse_world_units")
    if isinstance(max_allowed, bool) or not isinstance(max_allowed, (int,float)) or max_allowed <= 0:
        raise ValueError("Specify independently justified max_anchor_rmse_world_units > 0")
    measure = []
    for s in data.get("observations", []):
        before = transform(s["bond_before_pixel"])
        after = transform(s["bond_after_pixel"])
        diff = [after[i]-before[i] for i in range(2)]
        measure.append({
            "session":s["session"],
            "world_displacement":{"east":round(diff[0],6),"north":round(diff[1],6)},
            "world_before":{"east":round(before[0],6),"north":round(before[1],6)},
            "world_after":{"east":round(after[0],6),"north":round(after[1],6)},
            "bond_marks_source":s.get("bond_marks_source"),
            "camera_rotation_during_write":s.get("camera_rotation_during_write"),
            "collision_or_snap":s.get("collision_or_snap"),
            "landmark_geometry_valid":rmse <= max_allowed,
            "reference_type":"independent_world_frame" if rmse <= max_allowed else "unverified_geometry"
        })
    return {
        "protocol":"bond_landmark_v1_8",
        "affine_world_from_pixel":{"east":params[0],"north":params[1]},
        "landmark_rmse_world_units":round(rmse,6),
        "landmark_residuals":residuals,
        "map_geometry_accepted":rmse <= max_allowed,
        "observations":measure,
        "world_axis_identification":"not_established",
        "canonical_symbol_promoted":False,
        "limitations":["This calibrates an operator-defined 2D frame, not GoldenEye internal X/Z labels.",
                       "An FPS screenshot or projection of EC/F4 is not an independent world map.",
                       "Bond marker locations require independent surveying; affine model cannot locate Bond itself.",
                       "Landmark RMSE alone does not quantify Bond mark error or prove positional causality."]
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("survey",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=calibrate(json.loads(a.survey.read_text(encoding="utf-8")))
    output=a.output or a.survey.with_name(a.survey.stem+"_landmark_report.json")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Landmark audit:",output,"RMSE:",result["landmark_rmse_world_units"],
          "accepted:",result["map_geometry_accepted"],"observations:",len(result["observations"]))


if __name__=="__main__":
    main()
