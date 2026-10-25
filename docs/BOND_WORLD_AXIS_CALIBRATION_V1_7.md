# Bond Coordinate System Validation v1.7 — World-Axis Calibration

## Status and scientific boundary
**Implemented: offline world-frame comparison tool + prior-run manifest. Calibration itself awaits independently measured geometry.** Existing six v1.6 captures are successful isolated memory edits but only provide screen-relative directions. They CANNOT alone establish GoldenEye global axes X/Z.

### Previous six screen-relative observations
| Target | Signed float32 BE delta | Heading (operator relative) | Operator-observed movement | Session |
| EC | +128 | 0° | left | 20261025T021929Z_971338 |
| EC | +128 | 90° clockwise | backward | 20261025T024811Z_941631 |
| EC | +128 | ~180° | right | 20261025T023038Z_953512 |
| F4 | -128 | 0° | backward | 20261025T023714Z_940197 |
| F4 | -128 | 90° clockwise | right | 20261025T025126Z_942158 |
| F4 | -128 | ~180° | forward | 20261025T024117Z_941298 |

EC and F4 are still experimental candidates. The headings were operator-estimated, not independently measured by a validated yaw signal.

## What v1.7 adds
- `tools/calibrate_bond_world_axes_v1_7.py`: validates existing per-session `_coordinate_v1_6.json` audit, requires independently measured 2D **fixed-world** displacement vectors, normalizes vector sign by the actual float32 delta, compares angular separation for trials at headings separated by >=45 degrees; checks EC and F4 separately.
- `docs/BOND_WORLD_AXIS_V1_7_MANIFEST.json`: six historical sessions with screen observations only. Explicit `reference_type: screen_relative_only`, null world vectors and unverified headings prevent false "validated" claims.
- No new memory writes. Operator may continue existing `bond_position_discovery_v1_3.lua` capture and manual Cheat Search intervention. Every session must STOP before using the analyzers.

## Method: independent world reference (required for actual calibration)
1. Select an open room with fixed landmarks. Build an independent repeatable top-down coordinate reference, such as a separately calibrated map or known room-floor landmarks with fixed 2D positions. Label the *world* reference axes `east` and `north` purely as **local mapping conventions**, not yet game engine X/Z.
2. Save an original clean savestate with Bond in the same world position. Prepare separate heading 0/90/180/270 degree states **without translation**; measure rotations independently from landmarks or confirmed yaw field. No raw stick-duration assumption.
3. At each heading, capture isolated EC +128 and F4 -128 with the established v1.3 protocol. Each change starts from a documented identical world location (and no collision); measure the 2D position *before and after* in the independently calibrated fixed-world frame.
4. For each run update a copy of the manifest. Set `reference_type` to `independent_world_frame` only if justified. Fill `world_displacement: {"east": ..., "north": ...}` from physical measurements, NOT screen-relative arrows; record `landmark_or_map_method`, `heading_independently_verified: true`, `same_world_start_confirmed: true`, `camera_rotation_during_write: false`, and `collision_or_snap: false` only when actually supported. Include uncertainty/method notes separately if helpful.
5. To complete a fourth orientation run at 270° clockwise, append its new session as a separate manifest entry after analysis, not by overwriting historical rows.
6. Reproduction from independent sessions and validated ROM/N64 core identity remains required for canonical promotion.

### Standard capture and audit
Update repo and launch `bond_position_discovery_v1_3.lua` in BizHawk. Send each command individually, waiting for `MARKED` and the required stationary 120 frame holds:
```powershell
python -m tools.send_bond_position_v1_3 TARGET_EC
python -m tools.send_bond_position_v1_3 BASELINE
python -m tools.send_bond_position_v1_3 WRITE_PRE
# only now manually apply a small, verified edit to the chosen coordinate
python -m tools.send_bond_position_v1_3 WRITE_APPLIED
# keep still >=120 frames after write
python -m tools.send_bond_position_v1_3 WRITE_OBSERVE
python -m tools.send_bond_position_v1_3 STOP
# only after Lua reports DONE stop:
$sid=(Get-Content .\output\sessions\bond_position_v1_3_session.txt -Raw).Trim()
python -m tools.analyze_bond_position_v1_3 $sid
python -m tools.analyze_bond_coordinate_v1_6 $sid
```
For F4 use `TARGET_F4`. Do not rerun analyzers on the same session when output exists; they refuse overwriting.

### Offline calibration
Create a copy of the manifest (retain original provenance) and add verified world reference measurements:
```powershell
Copy-Item .\docs\BOND_WORLD_AXIS_V1_7_MANIFEST.json .\output\world_axes_v1_7_manifest.json
notepad .\output\world_axes_v1_7_manifest.json
python -m tools.calibrate_bond_world_axes_v1_7 .\output\world_axes_v1_7_manifest.json
Get-Content .\output\world_axes_v1_7_manifest_report.json
```
You can run the tool *right now* using the original or a copy: it should honestly report `insufficient_or_inconsistent_independent_world_geometry` because none of the historical sessions includes independent world geometry.

### Interpretation
- For **fixed world axes**: after sign-normalizing the intervention, measured fixed-world vectors for each address align across sufficiently different Bond headings. The analyzer reports maximum pairwise angular discrepancy independently for EC and F4. Exploratory <=15° agreement is reported as consistent, **not proof**.
- For **heading-relative components**: vectors in the calibrated world frame rotate with independently measured heading. Requires recorded vectors before claiming.
- Check approximately orthogonal EC/F4 vectors in the fixed-world reference to support separate horizontal axes. Do not assign internal labels X/Z based on arbitrary `east`/`north` conventions.
- For absent, unreliable or conflicting landmarks, the status must remain unresolved.

## Data integrity
- Prior operator reports are preserved as observation, not measurement.
- Reading/writing emulator RAM is unchanged (Lua observer remains read-only; any intervention is manual).
- No automatic promotion to `GoldenEye.mapping/catalog/symbols.json`.
- Same-world-start and verified heading fields must only be marked true after independent verification, never inferred from prior chat labels alone.
