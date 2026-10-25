# Bond World Landmark Discovery v1.8 — Independent Spatial Reference

## Scope
The previous v1.7 correctly returned `eligible: 0`: six EC/F4 memory interventions had heading-relative observations, but **no independently measured world positions**. This v1.8 introduces an offline, read-only 2D landmark registration tool. It is not a memory scanner and does not infer coordinates from screen-left/right arrows. No emulator writes are performed.

## What qualifies as independent
Use a **fixed overhead reference map** or independently surveyed room-floor plan with a known, reproducible scale and stationary orientation. Record at least 4 static, noncollinear fixed landmarks with (a) pixel coordinates on that map and (b) independently surveyed local coordinates (called east/north for convenience). These axis names are operator-chosen directions, not engine X/Z.

Record Bond's **position** before/after a single memory edit in that same map frame, using an independently verified mark (overhead camera marker, externally validated map locator, or other measured independent world position). The ordinary first-person gameplay screenshot is NOT by itself a map and cannot locate Bond in the world without a separately validated geometric solve. Avoid writing numbers produced by EC/F4 into the map/world positions: that would make the validation circular.

If no valid overhead map or Bond marker is accessible, leave `observation_source` unverified and `observations` empty. The correct outcome is **pending**, not fictitious calibration.

## Usage
```powershell
git pull --ff-only origin main
Copy-Item .\docs\BOND_LANDMARK_V1_8_SURVEY_TEMPLATE.json .\output\bond_landmark_v1_8_survey.json
notepad .\output\bond_landmark_v1_8_survey.json
python -m tools.discover_bond_world_landmarks_v1_8 .\output\bond_landmark_v1_8_survey.json
```

The bundled points are **illustrative, not actual GoldenEye landmarks**. Replace with real measured positions, establish scale, then set `observation_source: "independent_fixed_topdown_map"`, `fixed_map_and_scale_verified: true`, and retain `bond_coordinates_derived_from_ec_f4: false` **only if factually supported**. `max_anchor_rmse_world_units` is a user-defined justified acceptance threshold in the same arbitrary map units.

The script performs a least-squares affine fit from map pixels to east/north, reports coefficients, each landmark residual and RMSE, and transforms independently marked Bond before/after points to a 2D world displacement. It doesn't locate Bond automatically. It refuses source frames that are non-independent, degenerate landmark geometry, invalid numbers or overwriting reports.

## Planned capture sequence
1. Pick an open location with stable room landmarks, no collisions or camera movement during single write.
2. Acquire or calibrate the independent overhead map, establish 4+ fixed landmarks, record pixel/world pairs and survey error.
3. Restore the same Bond starting world location for each heading, and separately verify heading (0, 90, 180, 270 degrees are experimental labels until independently calibrated).
4. Perform EC +128 and F4 -128 single-field interventions with the existing read-only v1.3 capture; never send batch markers, wait for MARKED and DONE stop.
5. Export the `_coordinate_v1_6.json` audit for each fresh session, mark Bond position before/after independently in the same overhead image frame; if the marker can't be measured, record a blocker rather than fabricate a coordinate.
6. Use landmark transformation to compute `world_displacement`; link measured vector back into a copy of `output/world_axes_v1_7_manifest.json` **only after validation**.
7. For each genuinely independently validated run, set `reference_type="independent_world_frame"`, `heading_independently_verified=true`, `same_world_start_confirmed=true`, `camera_rotation_during_write=false`, `collision_or_snap=false`, and specify a detailed `landmark_or_map_method` if each statement is supported.
8. Re-run v1.7 calibrator on the edited manifest with a *new report path*. Do not overwrite previous reports.

## Interpretation / limits
- Passing anchor RMSE verifies a registration fit on supplied data; fabricated/sample points can also fit and confer **no empirical validation**.
- No method based only on moving background pixels in a first-person camera yields world displacement without additional camera pose and scene geometry.
- A video-based camera pose reconstruction might be another future reference, but would need independent intrinsic/extrinsic calibration, static 3D landmarks and quantified uncertainty.
- The local `east/north` frame is independent of candidate EC/F4 if separately surveyed; it does not establish internal axis names X/Z.
- Only v1.7 cross-heading alignment with independently measured world vectors can begin testing fixed-global-vs-relative coordinates; neither script promotes mapping symbols.

## Repository coordination
Development tools and runbook live in `GoldenEye.assistant`; provisional experimental evidence lives in `GoldenEye.mapping/experiments/bond_world_landmark_v1_8_20261024.json`. No changes to canonical symbols.
