# Spatial Physical Failure Diagnosis v3.6

## Scope

Read-only, retrospective audit of the existing **v3.5** hold-differentials CSV. No new Lua capture, game-memory write, retuning of v3.5 gates, or change to `GoldenEye.mapping`. The result is **failure diagnostics**, not XYZ coordinates.

The v3.5 report can omit a session/offset/interpretation when any hold decode is nonfinite. That omission does **not** establish why a particular field was rejected; missing entries are **not evaluable**, rather than physical test failures.

## Run (PowerShell, from repository root)

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_failure_v3_6 -v
$original='20261024T152944Z_311185'
$replica='20261024T171358Z_645378'
$third='20261024T182827Z_912356'
$fourth='20261024T184544Z_974402'
python .\tools\analyze_spatial_failure_v3_6.py $original $replica $third $fourth
```

Inputs: `output/csv/spatial_v3_5_<id1>__..._<idN>_hold_differentials.csv`, in exactly the same session order as the command. Must already exist. The expected grid is **20 aligned offsets × 4 interpretations × N sessions**. For four sessions: 320 combinations; the supplied v3.5 run had 277 rows, therefore **43 missing combinations**, not 27. The earlier count of 76 refers to offset/kind combinations *present in at least one session*, not the full search space of 80. All missing rows are reported separately. Each v3.5 row is checked for valid binary decisions and consistency of its `candidate` flag with the conjunction.

Outputs, never overwritten:

- `spatial_v3_6_..._failure_details.csv`: complete 320-row grid; individual gate failures; `not_evaluable` when v3.5 supplied no row; original five-hold values/deltas/ratios.
- `spatial_v3_6_..._cross_session_failures.csv`: per offset/kind counts for each failed criterion, including missing records.
- `spatial_v3_6_..._summary.json`: per-session number evaluated, missing, passed, failure counts; global totals and explicit caveats.

For the user's v3.5 diagnostic, `second_step_nonzero` is **misleadingly named**: it tests that **all three** displacements (`step1`, `back`, and `step2`) exceed both EPS and 10 × hold MAD. v3.6 explicitly names that criterion `movement_amplitude`; no algorithmic change to v3.5 is implied.

The heuristic hints `constant_or_low_movement`, `tiny_le_f32_values_check_endianness`, and `movement_pattern_not_position_proof` are descriptive only. A very small little-endian value is not by itself proof of the wrong endianness. This v3.6 works from aggregated CSV values and **cannot reconstruct original raw hex bytes** or precisely diagnose a missing nonfinite field; that would require revisiting raw captures in a future version.

## Interpretation and limitations

Failing `direction_reversed`, `return_close`, `rotation_unchanged`, `holds_stable` or `movement_amplitude` describes a **v3.5 criterion**, not a demonstrated hardware/game cause. No criterion is relaxed to force a passing coordinate. Reports cannot distinguish Bond/camera/animation/velocity or verify actual travel distances or heading; external positional ground truth is still absent.

The original v2.4 CSVs, v3.5 CSVs, and `GoldenEye.mapping` must remain unchanged.
