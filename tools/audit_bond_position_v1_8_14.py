"""Bond Position v1.8.14: spatial return and alias divergence audit (read-only offline).

Use an existing v1.8.13 timeline. No confirmed world position, axis or identity.
"""
import argparse
import csv
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path

ALIASES = ((0x06D248, 0x0D33EC), (0x06D250, 0x0D33F4))
PRIMARY = (0x06D248, 0x06D250)
ALTERNATE = (0x0D33EC, 0x0D33F4)
ROUTES = (("MOVE_FORWARD", "MOVE_BACK"),
          ("MOVE_FORWARD_REPEAT", "MOVE_BACK_REPEAT"))
STILLS = ("ORIGIN_STILL", "ORIGIN_AFTER_ROTATION", "DESTINATION_STILL",
          "RETURN_STILL", "DESTINATION_REPEAT_STILL", "RETURN_REPEAT_STILL")


def _decode(raw):
    try:
        value = struct.unpack(">f", bytes.fromhex(raw))[0]
        return value if math.isfinite(value) and abs(value) < 1e8 else None
    except (TypeError, ValueError, struct.error):
        return None


def _vector(start, end):
    return [end[0] - start[0], end[1] - start[1]]


def _norm(v):
    return math.hypot(*v)


def _audit_route(rows, fwd, back, pair):
    def data(phase):
        return [(n, *[_decode(values.get(o)) for o in pair])
                for n, label, values in rows if label == phase]
    a = [x for x in data(fwd) if all(v is not None for v in x[1:])]
    b = [x for x in data(back) if all(v is not None for v in x[1:])]
    if len(a) < 2 or len(b) < 2:
        return {"available": False, "forward_frames": len(a), "backward_frames": len(b)}
    forward = _vector(a[0][1:], a[-1][1:])
    backward = _vector(b[0][1:], b[-1][1:])
    fa, ba = _norm(forward), _norm(backward)
    dot = sum(x*y for x, y in zip(forward, backward))
    return {
        "available": True, "forward_frames": len(a), "backward_frames": len(b),
        "forward_vector": forward, "backward_vector": backward,
        "forward_length": fa, "backward_length": ba,
        "opposition_cosine": dot/(fa*ba) if fa > 0 and ba > 0 else None,
        "vector_sum": [forward[0]+backward[0], forward[1]+backward[1]],
        "vector_closure_error": _norm([forward[0]+backward[0], forward[1]+backward[1]]),
        "closure_ratio_to_forward": _norm([forward[0]+backward[0], forward[1]+backward[1]])/fa if fa > 0 else None,
        "interpretation": "numeric_displacement_only"
    }


def analyze(sid, root=Path("output/csv")):
    if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):
        raise ValueError("invalid session")
    stem = Path(root)/f"bond_position_v1_8_13_{sid}"
    with Path(str(stem)+"_timeline.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"session", "frame", "phase", "offset_hex", "raw_be"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("incomplete timeline header")
        frames = defaultdict(dict)
        phases = {}
        for record in reader:
            if record["session"] != sid:
                raise ValueError("foreign session")
            n = int(record["frame"])
            offset = int(record["offset_hex"],16)
            if offset in frames[n]:
                raise ValueError("duplicate frame offset")
            frames[n][offset] = record["raw_be"]
            if n in phases and phases[n] != record["phase"]:
                raise ValueError("inconsistent phase")
            phases[n] = record["phase"]
    if not frames:
        raise ValueError("empty timeline")
    ordered = sorted(frames)
    rows = [(n, phases[n], frames[n]) for n in ordered]
    gaps = [[a,b] for a,b in zip(ordered,ordered[1:]) if b != a+1]
    alias_results = []
    divergence_frames = []
    for left,right in ALIASES:
        valid = [(n, phases[n], frames[n][left], frames[n][right])
                 for n in ordered if left in frames[n] and right in frames[n]]
        disagreements = [(n,p,a,b) for n,p,a,b in valid if a != b]
        phase_counts = Counter(p for _,p,_,_ in disagreements)
        lag_matches = {}
        # Compare one-frame shifted values ONLY on contiguous frames, for diagnostic latency.
        for lag in (-2,-1,1,2):
            eligible = [(n,a,frames[n+lag][right]) for n,_,a,_ in valid
                        if n+lag in frames and right in frames[n+lag]
                        and abs(lag)<=2]
            lag_matches[str(lag)] = {
                "frames_compared":len(eligible),
                "raw_equal_fraction":sum(a == b for _,a,b in eligible)/len(eligible) if eligible else None
            }
        for n,p,a,b in disagreements:
            prev = frames.get(n-1)
            nxt = frames.get(n+1)
            divergence_frames.append({
                "frame":n,"phase":p,"left":f"0x{left:06X}","right":f"0x{right:06X}",
                "left_raw":a,"right_raw":b,
                "left_float_be":_decode(a),"right_float_be":_decode(b),
                "left_previous_equals_right_now":bool(prev and left in prev and prev[left]==b),
                "right_previous_equals_left_now":bool(prev and right in prev and prev[right]==a),
                "left_next_equals_right_now":bool(nxt and left in nxt and nxt[left]==b),
                "right_next_equals_left_now":bool(nxt and right in nxt and nxt[right]==a),
                "marker_transition_frame":bool(n-1 in phases and phases[n-1]!=p)
            })
        alias_results.append({
            "left":f"0x{left:06X}","right":f"0x{right:06X}",
            "frames_compared":len(valid),"divergence_count":len(disagreements),
            "equal_fraction":1-len(disagreements)/len(valid) if valid else None,
            "divergences_by_phase":dict(phase_counts),
            "lag_diagnostics":lag_matches
        })
    routes={}
    for pair_name,pair in (("primary",PRIMARY),("alias",ALTERNATE)):
        routes[pair_name]={f"{fwd}_vs_{back}":_audit_route(rows,fwd,back,pair)
                           for fwd,back in ROUTES}
    return {
        "protocol":"bond_position_spatial_return_alias_audit_v1_8_14",
        "source_protocol":"bond_position_v1_8_13",
        "session":sid,"frames":len(ordered),"gaps":gaps,
        "aliases":alias_results,"divergence_frames":divergence_frames,
        "routes":routes,
        "physical_return_validated":False,"world_coordinates_validated":False,
        "alias_latency_validated":False,
        "limitations":[
            "Operator-directed movement and visual return-to-origin were not independently measured.",
            "Vector opposition does not imply closure; closure does not establish a physical coordinate frame.",
            "Lagged raw agreement can arise from smooth or constant series; compare transition-local details.",
            "The collector reads fields sequentially per frame, not atomically.",
            "Fields and entity identity remain experimental."
        ]
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("output/csv"))
    a=p.parse_args()
    result=analyze(a.session,a.root)
    target=a.root/f"bond_position_v1_8_14_{a.session}_analysis.json"
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Bond position v1.8.14",target,"frames",result["frames"],
          "divergences",len(result["divergence_frames"]))


if __name__=="__main__":
    main()
