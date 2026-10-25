"""Soldier relative-coordinate audit v1.8.1; offline, read-only.

Requires operator measurements, a v1.6 Bond audit and soldier candidate samples.
Freeze cheat ON is a control, not proof of stationary world coordinates.
"""
import argparse
import json
import math
from pathlib import Path

EC, F4 = "0x0D33EC", "0x0D33F4"

def number(v, label):
    if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
        raise ValueError(f"{label}: numeric finite value required")
    return float(v)

def point(v, label):
    if not isinstance(v, dict):
        raise ValueError(f"{label}: object required")
    return (number(v.get("u"),label+".u"),number(v.get("v"),label+".v"))

def analyze(data, audit_dir=Path("output/csv")):
    if data.get("protocol") != "bond_soldier_relative_v1_8_1":
        raise ValueError("Unknown protocol")
    output = []
    for run in data.get("runs",[]):
        sid=run["bond_session"]
        if not sid or any(c in sid for c in "/\\") or ".." in sid:
            raise ValueError("Unsafe session")
        audit=json.loads((audit_dir/f"bond_position_v1_3_{sid}_coordinate_v1_6.json").read_text(encoding="utf-8"))
        changes=audit.get("candidate_changes",[])
        bond_ok=(audit.get("isolated_memory_effect") is True and len(changes)==1 and
                 audit.get("target") in (EC,F4) and audit["target"]==run.get("bond_target"))
        delta=number(changes[0]["float32_be_delta"],"bond delta") if bond_ok else None
        freeze=run.get("freeze",{})
        freeze_ok=(freeze.get("on_verified_before") is True and
                   freeze.get("on_verified_after") is True and
                   freeze.get("no_toggle_during_trial") is True and
                   freeze.get("enemy_identity_stable") is True)
        soldier=run.get("soldier",{})
        source=soldier.get("source")
        coordinate_verified=soldier.get("coordinate_candidate_independently_validated") is True
        # A soldier may be frozen by AI while its animation/position differs.
        pre=point(soldier["before"],"soldier before")
        post=point(soldier["after"],"soldier after")
        drift=math.dist(pre,post)
        limit=number(run.get("max_stationarity_drift"),"max_stationarity_drift")
        if limit < 0:
            raise ValueError("Negative drift threshold")
        stationary=freeze_ok and drift<=limit and coordinate_verified
        # Bond's before/after positions in the soldier coordinate system must
        # be INDEPENDENTLY measured, not read from target EC/F4 or inferred by
        # subtracting the expected delta.
        bond=run.get("bond_in_soldier_frame",{})
        independent=(bond.get("independent_measurement") is True and
                     bond.get("derived_from_ec_f4") is False and
                     bond.get("frame_matches_soldier") is True)
        rel=None
        if independent:
            bp=point(bond["before"],"bond before")
            ap=point(bond["after"],"bond after")
            rel_before=[pre[i]-bp[i] for i in range(2)]
            rel_after=[post[i]-ap[i] for i in range(2)]
            rel={"before":rel_before,"after":rel_after,
                 "delta":[rel_after[i]-rel_before[i] for i in range(2)],
                 "bond_delta":[ap[i]-bp[i] for i in range(2)],
                 "inverse_agreement_error": math.hypot(*[(rel_after[i]-rel_before[i])+(ap[i]-bp[i]) for i in range(2)])}
        eligible=bool(bond_ok and stationary and independent and rel is not None and
                      source=="independent_enemy_position_candidate")
        output.append({"bond_session":sid,"bond_target":audit.get("target"),
                       "bond_delta":delta,"bond_audit_isolated":bond_ok,
                       "freeze_state_verified":freeze_ok,
                       "soldier_id":soldier.get("id"),
                       "soldier_coordinate_candidate":soldier.get("candidate"),
                       "soldier_drift":drift,"drift_limit":limit,
                       "soldier_stationary_validated":stationary,
                       "independent_bond_position_available":independent,
                       "relative_vector":rel if eligible else None,
                       "eligible_spatial_reference":eligible,
                       "classification":"independent_relative_reference_candidate" if eligible
                            else "insufficient_independent_spatial_measurements"})
    return {"protocol":"bond_soldier_relative_v1_8_1","runs":output,
            "eligible_runs":sum(x["eligible_spatial_reference"] for x in output),
            "canonical_axis_validated":False,"canonical_symbol_promoted":False,
            "limitations":["Freeze All Enemies Alive may stop AI without proving world-position immobility.",
                           "Enemy coordinate candidates need independent validation; no assumed RAM offsets.",
                           "Bond position in the same coordinate frame must be measured independently of EC/F4.",
                           "A soldier's FPS screen pixel is not a calibrated world position.",
                           "A verified relative vector still does not determine native X/Z axis labels."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--audit-dir",type=Path,default=Path("output/csv"))
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    report=analyze(json.loads(args.manifest.read_text(encoding="utf-8")),args.audit_dir)
    out=args.output or args.manifest.with_name(args.manifest.stem+"_report.json")
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Soldier reference audit:",out,"eligible:",report["eligible_runs"],
          "runs:",len(report["runs"]))
if __name__=="__main__":
    main()
