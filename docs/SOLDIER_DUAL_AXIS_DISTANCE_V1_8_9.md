# Soldier Coordinate Discovery v1.8.9 — Dual-Axis Distance Convergence

**Goal.** Test whether two *hypothetical*, paired float32 big-endian components associated with Bond and Soldier #1 simultaneously converge during `BOND_APPROACH` and diverge during `BOND_RETREAT`. This is an **offline, read-only** analysis of the existing v1.8.8.1 CSV capture, *not* a validation of physical X/Z coordinates.

## Candidate configurations

- `historical`: Bond `0x06D248` / `0x06D250`, Soldier `0x20F594` / `0x20F5AC`
- `alternate`: Bond `0x06D248` / `0x06D250`, Soldier `0x20F578` / `0x20F580`
- `duplicate_region`: Bond `0x06D248` / `0x06D250`, Soldier `0x06A120` / `0x06A128`
- `bond_alias_historical`: Bond `0x0D33EC` / `0x0D33F4`, Soldier `0x20F594` / `0x20F5AC`

For each recorded frame in which all four values are finite, the analyzer computes signed differences A/B and `hypot(delta_a, delta_b)` **using those values from the same frame**. It records first/last/minimum candidate distance per phase and the exact frame and component differences at each phase's minimum. No combination of minima from different times is allowed.

## Reuse captured session

From the `GoldenEye.assistant` repository root:

```powershell
git pull --ff-only origin main
python -m unittest tests.test_soldier_dual_axis_v1_8_9 -v
$sid = "20261025T171426Z_33465"
python -m tools.analyze_soldier_dual_axis_v1_8_9 $sid
$r = Get-Content ".\output\csv\soldier_dual_axis_v1_8_9_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.configs | ForEach-Object {
    [PSCustomObject]@{
        pair = $_.name
        approach_start = $_.phase_metrics.BOND_APPROACH.first_distance
        approach_end = $_.phase_metrics.BOND_APPROACH.last_distance
        approach_min = $_.phase_metrics.BOND_APPROACH.minimum_distance
        min_frame = $_.phase_metrics.BOND_APPROACH.minimum_frame
        retreat_end = $_.phase_metrics.BOND_RETREAT.last_distance
        converged = $_.approach_converged
        diverged = $_.retreat_diverged
    }
} | Format-Table -AutoSize
```

Run the analyzer only once per `sid` unless the prior generated report is intentionally moved to a backup path; existing output is never overwritten.

## Interpretation / constraints

- A decrease from phase start to end is not proof of monotonic change. Values may converge coincidentally.
- The soldier can move independently, and the Bond and Soldier coordinates remain **unvalidated hypotheses**.
- `float32_big_endian` and shared numeric units are working assumptions, not proofs.
- The RDRAM observer sampled individual fields sequentially during a single emulated frame; this does not establish atomicity.
- Independent Soldier #1 identification, world-position geometry, and repeat saves are required for confirmation.
- `GoldenEye.mapping` canonical symbols remain unchanged.
