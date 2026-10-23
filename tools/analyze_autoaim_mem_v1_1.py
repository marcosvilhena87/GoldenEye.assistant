"""Compare six control snapshots in v1.1 and intersect with v1 candidates.

All reported locations are memory-domain offsets, not validated auto-aim symbols.
"""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("A1", "A_STABLE", "B", "B_STABLE", "A2", "CONTROL_A")

def manifest_entries(path, session=None):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Empty manifest: {path}")
    sid = session or rows[-1]["session"]
    selected = [r for r in rows if r["session"] == sid]
    if [r["label"] for r in selected] != list(LABELS):
        raise ValueError(f"Session {sid}: expected labels {LABELS}, found {[r['label'] for r in selected]}")
    if len({(r["domain"], r["size"]) for r in selected}) != 1:
        raise ValueError("Domain or size mismatch")
    return sid, selected

def safe_file(rel):
    path = (ROOT / rel).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Unsafe path")
    return path

def candidate_set(path):
    with path.open(newline="", encoding="utf-8") as f:
        return {int(row["offset_hex"],16) for row in csv.DictReader(f)}

def analyze(session=None, previous=None):
    sid, entries = manifest_entries(ROOT / "output/csv/autoaim_mem_v1_1_manifest.csv", session)
    size = int(entries[0]["size"])
    buffers = [safe_file(r["path"]).read_bytes() for r in entries]
    if any(len(b) != size for b in buffers):
        raise ValueError("Snapshot missing/incomplete or incorrect size")
    prior = candidate_set(previous) if previous else None
    if prior is not None:
        previous_manifest = ROOT / "output/csv/autoaim_mem_v1_manifest.csv"
        if previous_manifest.exists():
            with previous_manifest.open(newline="", encoding="utf-8") as f:
                matches = [r for r in csv.DictReader(f) if r["session"] in previous.name]
            if matches and (matches[0]["domain"] != entries[0]["domain"] or int(matches[0]["size"]) != size):
                raise ValueError("v1 and v1.1 domains or sizes are different")
    output = ROOT / "output/csv" / f"autoaim_mem_v1_1_candidates_{sid}.csv"
    counts = {"a1_b_changed":0,"stable_on":0,"stable_off":0,"negative_control_pass":0,"strict":0,"intersect_previous":0}
    with output.open("w",encoding="utf-8",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("session","domain","offset_hex","on_byte","off_byte","in_v1_candidates","status"))
        for i, vals in enumerate(zip(*buffers)):
            a1, a_stable, b, b_stable, a2, control_a = vals
            if a1!=b: counts["a1_b_changed"]+=1
            if a1==a_stable: counts["stable_on"]+=1
            if b==b_stable: counts["stable_off"]+=1
            if a2==control_a: counts["negative_control_pass"]+=1
            if a1==a_stable==a2==control_a and b==b_stable and a1!=b:
                counts["strict"]+=1
                in_previous = prior is not None and i in prior
                if in_previous: counts["intersect_previous"]+=1
                writer.writerow((sid,entries[0]["domain"],f"0x{i:06X}",a1,b,
                                 "yes" if in_previous else ("no" if prior is not None else "not_checked"),
                                 "candidate_control_filtered_only"))
    print(f"Session: {sid} domain: {entries[0]['domain']} bytes: {size}")
    for key,value in counts.items():
        if key=="intersect_previous" and prior is None:continue
        print(f"{key}: {value}")
    print(f"CSV: {output}")
    print("WARNING: correlation and repeatability are not causality; ROM hash/core and further negative controls are needed.")
    return counts, output

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--session",help="v1.1 session ID (defaults to most recent)")
    parser.add_argument("--previous-v1-csv",type=Path,help="v1 candidate CSV to intersect; must be from matching domain and ROM/core")
    args=parser.parse_args()
    try:
        analyze(args.session,args.previous_v1_csv)
    except (OSError,ValueError,KeyError) as exc:
        parser.exit(1,f"ERROR: {exc}\n")
