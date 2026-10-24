"""v3.6 retrospective failure diagnosis for immutable v3.5 physical-position CSVs.

No RDRAM writes, threshold tuning, coordinate validation, or canonical mapping edits.
The v3.5 flag second_step_nonzero actually means *all three steps meaningful*.
"""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

KINDS = ("be_f32", "le_f32", "be_i32", "be_u32")
CRITERIA = ("movement_amplitude", "direction_reversed", "return_close",
            "rotation_unchanged", "holds_stable")
DETAIL_FIELDS = ("session", "offset", "kind", "status", "failed_count",
                 "failed_criteria", "movement_amplitude", "direction_reversed",
                 "return_close", "rotation_unchanged", "holds_stable",
                 "step1", "back", "step2", "return_error_ratio",
                 "rotation_error_ratio", "max_hold_mad_ratio",
                 "p0", "p1", "p0_return", "p0_rotated", "p2",
                 "v35_candidate", "v36_all_pass", "interpretation_hint")
CROSS_FIELDS = ("offset", "kind", "observed_sessions", "missing_sessions",
                "passing_sessions", "all_session_pass", "failure_counts",
                "decision")
REQUIRED = ("session", "offset", "kind", "second_step_nonzero",
            "direction_reversed", "return_close", "rotation_unchanged",
            "holds_stable", "candidate", "step1", "back", "step2",
            "return_error_ratio", "rotation_error_ratio",
            "max_hold_mad_ratio", "p0", "p1", "p0_return", "p0_rotated", "p2")

def flag(raw, field):
    value = str(raw[field]).strip()
    if value not in ("0", "1"):
        raise ValueError(f"Invalid binary flag {field}={value!r}")
    return int(value)

def number(raw, field):
    try:
        x = float(raw[field])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric {field}={raw[field]!r}") from exc
    if not math.isfinite(x):
        raise ValueError(f"Nonfinite {field}: {x}")
    return x

def read_v35(path, sessions):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError("Not a v3.5 hold_differentials CSV; required columns missing")
        result = {}
        for raw in reader:
            session = raw["session"]
            if session not in sessions:
                raise ValueError("Unexpected session in input: " + session)
            key = (session, raw["offset"], raw["kind"])
            if raw["kind"] not in KINDS:
                raise ValueError("Unexpected numeric interpretation: " + raw["kind"])
            if not raw["offset"].startswith("0x"):
                raise ValueError("Invalid offset: " + raw["offset"])
            if key in result:
                raise ValueError("Duplicate session/offset/kind: " + str(key))
            result[key] = raw
    return result

def classify(raw, session, offset, kind):
    if raw is None:
        row = {k: "" for k in DETAIL_FIELDS}
        row.update(session=session, offset=offset, kind=kind, status="not_evaluable",
                   failed_count="", failed_criteria="missing_v35_row",
                   v36_all_pass=0, interpretation_hint="no_finite_five_hold_decode")
        return row
    flags = dict(movement_amplitude=flag(raw, "second_step_nonzero"),
                 **{k: flag(raw, k) for k in CRITERIA[1:]})
    failed = [key for key in CRITERIA if not flags[key]]
    old = flag(raw, "candidate")
    passed = int(not failed)
    if old != passed:
        raise ValueError("v3.5 flag inconsistency at " + str((session, offset, kind)))
    values = {name: number(raw, name) for name in
              ("step1", "back", "step2", "return_error_ratio",
               "rotation_error_ratio", "max_hold_mad_ratio",
               "p0", "p1", "p0_return", "p0_rotated", "p2")}
    hint = ("constant_or_low_movement" if all(abs(values[k]) <= 1e-6
            for k in ("step1", "back", "step2")) else
            "movement_pattern_not_position_proof")
    if kind == "le_f32" and all(abs(values[k]) < 1e-30
                                for k in ("step1", "back", "step2")):
        hint = "tiny_le_f32_values_check_endianness"
    row = {k: raw.get(k, "") for k in DETAIL_FIELDS}
    row.update(session=session, offset=offset, kind=kind,
               status="evaluated", failed_count=len(failed),
               failed_criteria=";".join(failed) if failed else "none",
               **flags, v35_candidate=old, v36_all_pass=passed,
               interpretation_hint=hint)
    return row

def diagnose(raw_rows, sessions):
    # Complete expected grid (20 aligned addresses x 4 interpretations) even if
    # v3.5 skipped nonfinite representations. Nothing missing is treated as pass.
    offsets = [f"0x{x:06X}" for x in range(0x3B30B0, 0x3B3100, 4)]
    expected = {(s, o, k) for s in sessions for o in offsets for k in KINDS}
    extra = set(raw_rows) - expected
    if extra:
        raise ValueError("Out-of-window data: " + str(sorted(extra)[:3]))
    details = [classify(raw_rows.get((s, o, k)), s, o, k)
               for s in sessions for o in offsets for k in KINDS]
    cross = []
    for o in offsets:
        for k in KINDS:
            group = [x for x in details if x["offset"] == o and x["kind"] == k]
            missing = [x["session"] for x in group if x["status"] == "not_evaluable"]
            counts = Counter()
            for x in group:
                for fail in x["failed_criteria"].split(";"):
                    if fail and fail != "none":
                        counts[fail] += 1
            passed = sum(int(x["v36_all_pass"]) for x in group)
            cross.append(dict(offset=o, kind=k,
                              observed_sessions=len(sessions)-len(missing),
                              missing_sessions=";".join(missing),
                              passing_sessions=passed,
                              all_session_pass=int(passed == len(sessions)),
                              failure_counts=json.dumps(dict(sorted(counts.items())),
                                                        sort_keys=True),
                              decision=("diagnostic_all_pass_not_validated" if
                                        passed == len(sessions) else "not_supported")))
    by_session = {}
    for s in sessions:
        rows = [r for r in details if r["session"] == s]
        counts = Counter()
        for r in rows:
            for fail in r["failed_criteria"].split(";"):
                if fail and fail != "none":
                    counts[fail] += 1
        by_session[s] = dict(expected=len(rows),
                             evaluated=sum(r["status"] == "evaluated" for r in rows),
                             missing=sum(r["status"] == "not_evaluable" for r in rows),
                             passing=sum(int(r["v36_all_pass"]) for r in rows),
                             failures=dict(sorted(counts.items())))
    summary = dict(schema="spatial_failure_diagnosis_v3_6",
                   sessions=list(sessions), per_session=by_session,
                   expected_total=len(details),
                   evaluated_total=sum(x["status"] == "evaluated" for x in details),
                   missing_total=sum(x["status"] == "not_evaluable" for x in details),
                   cross_session_all_pass=sum(x["all_session_pass"] for x in cross),
                   semantics={"movement_amplitude": "v3.5 second_step_nonzero: all THREE movement magnitudes exceed noise and EPS",
                              "missing_v35_row": "v3.5 omitted an interpretation; likely nonfinite during one or more holds, reason not preserved in CSV",
                              "interpretation_hint": "heuristic only, not field identification"},
                   limitation="No external positional ground truth; cannot validate Bond XYZ.")
    return details, cross, summary

def run(sessions, root=Path(".")):
    if len(sessions) < 2 or len(set(sessions)) != len(sessions):
        raise ValueError("At least two distinct sessions required")
    folder = Path(root) / "output" / "csv"
    ids = "__".join(sessions)
    source = folder / ("spatial_v3_5_" + ids + "_hold_differentials.csv")
    rows = read_v35(source, set(sessions))
    details, cross, summary = diagnose(rows, sessions)
    stem = folder / ("spatial_v3_6_" + ids)
    paths = [Path(str(stem) + suffix) for suffix in
             ("_failure_details.csv", "_cross_session_failures.csv", "_summary.json")]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite v3.6 reports")
    for path, fields, data in zip(paths[:2], (DETAIL_FIELDS, CROSS_FIELDS),
                                  (details, cross)):
        with path.open("x", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    with paths[2].open("x", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    return paths, summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="+")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    paths, summary = run(args.sessions, args.root)
    for path in paths:
        print("Wrote", path)
    print("Evaluated:", summary["evaluated_total"], "Missing:", summary["missing_total"])
    print("Cross-session all pass:", summary["cross_session_all_pass"])
    print(summary["limitation"])
