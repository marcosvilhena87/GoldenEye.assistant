# Axis-Aware Position Discovery v3.7

Retrospective and read-only, using the existing v3.5 `_hold_differentials.csv`. No Lua changes, no new capture required, no change to `GoldenEye.mapping`.

## Why

The v3.5 `second_step_nonzero` flag required *all three* increments to be significant. A single physical axis may be unchanged after turning to a different heading. v3.7 independently tests step 1 and step 2 without lowering the previously declared hold-noise, return or rotation limits.

## Gates

- Recover approximate hold MAD from v3.5 ratio: `noise = max_hold_mad_ratio × max(|step1|, |back|, |step2|, 1e-6)`.
- An individual movement is significant only if `abs(delta) > max(1e-6, 10 × noise)`.
- At least one of first or second movement must be significant.
- If first movement is significant, the return must reverse sign and `return_error_ratio <= .1`. If not significant, the return leg must be near zero and total displacement back to P0 <=10% of movement scale. This prevents a second-axis-only false positive caused by large drift.
- Rotation error ratio <= .1 and hold MAD ratio <= .02, unchanged from v3.5.
- An axis candidate must pass all supplied sessions with a reproducible response on **at least one common movement**, either first or second.
- Pairs must use different offsets, pass individual cross-session gates, and yield a normalized displacement determinant >= .1 in **every** session. This is an uncalibrated noncollinearity proxy, not a proof of X/Y.

The method can still reject real axes if the manual return was imperfect, if game movement isn't aligned with the chosen axes, or if the static RDRAM window does not contain the positions. Independent external measurement, Bond-vs-camera discrimination, byte-level reinspection and calibration remain necessary.

## Run from Windows PowerShell in repository root

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_axes_v3_7 -v
$original='20261024T152944Z_311185'
$replica='20261024T171358Z_645378'
$third='20261024T182827Z_912356'
$fourth='20261024T184544Z_974402'
python .\tools\analyze_spatial_axes_v3_7.py $original $replica $third $fourth
```

Outputs (new files, no overwrite):

- `spatial_v3_7_..._axis_responses.csv`: one complete row per 20 offsets × 4 interpretations × session; axis role (`first_only`, `second_only`, `both`, `neither`), gate failure reasons and missing-v3.5 flags.
- `spatial_v3_7_..._cross_session_axes.csv`: number of passing sessions for each representation, plus common-direction consistency.
- `spatial_v3_7_..._axis_pairs.csv`: candidate pair results for independently selected offsets (may contain zero rows).
- `spatial_v3_7_..._summary.json`: metrics and caveats.

All reports are audit artefacts. Neither `axis_candidate_not_validated` nor `two_axis_candidate_not_validated` constitutes external physical validation.
