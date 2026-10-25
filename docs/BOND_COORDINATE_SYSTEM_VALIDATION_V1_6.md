# Bond Coordinate System Validation v1.6 — Global Axes vs Bond-Relative Directions

**Status: experimental protocol ready, tests pending.** Never promote symbols based solely on these tests.

## Established experimental basis
- EC at `0x0D33EC`: float32 big-endian changes -128/-128/+128, with operator-observed forward/forward/backward motion at the sampled heading.
- F4 at `0x0D33F4`: +128/-128, with operator-observed left/right motion; EC was constant in both write windows.
- Neither proves whether EC/F4 are global X/Z components. All screen-direction labels are **at one heading**, not world axes. Do not equate screen motion with world motion without fixed landmarks and orientation control.
- Source experiments: `GoldenEye.mapping/experiments/bond_position_reversibility_v1_4_20261024.json`, `bond_position_second_axis_v1_5_20261024.json`.

## Hypotheses
H_global: EC and F4 are independent fixed world axes. Their displacement vector in world geometry is invariant as Bond rotates. Screen-relative direction may change with heading/camera.
H_relative: each component is related to Bond's local forward/lateral orientation; its displacement vector rotates with Bond's heading or otherwise depends on orientation.
H_confounded: camera changes, auto-position correction, collision, or savestate difference make observations uninterpretable.

## Important geometry distinction
GoldenEye is first-person: the image is rendered from Bond/camera's viewpoint. Translating the camera can make static scenery move in the **opposite direction** to Bond's world translation. Screen-left movement of scenery does not, by itself, mean Bond moved left in world space. The operator must reference fixed walls/objects and describe whether *Bond* or the scenery moved; a fixed world minimap/reference, if available, is stronger. Rotating Bond changes the image even if world coordinates remain constant.

## Experimental matrix
Perform isolated writes from identical original savestate at each *heading*:
| Heading relative to initial | EC signed edit | F4 signed edit | Controls |
| 0 degrees | - and + | - and + | no-write baseline |
| 90 degrees clockwise | - and + | - and + | no-write baseline |
| 180 degrees | - and + | - and + | no-write baseline |
| 270 degrees clockwise (optional, useful) | - and + | - and + | no-write baseline |

Minimum informative set: headings 0, 90, 180, and one signed edit for each axis at each heading (6 clean runs), plus same-savestate no-write baselines. Reverse-sign controls at 0 and at least one rotated heading strongly advised.

Use the *same scene and reproducible world starting point*, saving separate heading-specific clean savestates with no cheats enabled. Record heading orientation using visible world landmarks or validated heading field. Never assume rotating 90 degrees based on uncontrolled analog stick duration: estimate/verify relative rotation. Exact cardinal headings are useful but not required if measured accurately.

## One isolated run: existing v1.3 capture
1. Restore the clean savestate with heading and location documented; confirm no active previous cheats. STOP any prior Lua observer before loading.
2. Start `bond_position_discovery_v1_3.lua`; wait for session ID.
3. Send `TARGET_EC` or `TARGET_F4` and wait for `MARKED`; send `BASELINE`, allow >=120 stationary frames, and wait for MARKED.
4. Send `WRITE_PRE`, wait for MARKED, document before-hex EC/F4 and visual landmarks. Change **only the selected** verified RAM field once via Cheat Search, using *small reversible delta*, never blindly reusing previous hex. Confirm no collision/out-of-bounds and no camera rotation.
5. Send `WRITE_APPLIED` right after the edit; keep hands off for >=120 emulated frames; send `WRITE_OBSERVE`, then `STOP`, checking MARKED and DONE stop.
6. Audit the raw event frame, signed float32 delta, unchanged non-target coordinate, alias agreement, frame-relative 1/30/120 stability, and scene/camera response. Restart independently from original savestate for next cell.
7. To test **heading-only control**, rotate Bond without changing position, wait for stationary scene, capture both fields and note whether camera direction and displacement interpretation changed; do not conflate this with coordinate writes.

## PowerShell commands — individually, waiting for MARKED
```powershell
git pull --ff-only origin main
# Start bond_position_discovery_v1_3.lua in Lua Console after creating output dirs
python -m tools.send_bond_position_v1_3 TARGET_EC
python -m tools.send_bond_position_v1_3 BASELINE
python -m tools.send_bond_position_v1_3 WRITE_PRE
# MANUALLY edit chosen field after WRITE_PRE is acknowledged
python -m tools.send_bond_position_v1_3 WRITE_APPLIED
# >=120 frames without inputs
python -m tools.send_bond_position_v1_3 WRITE_OBSERVE
python -m tools.send_bond_position_v1_3 STOP
$sid=(Get-Content .\output\sessions\bond_position_v1_3_session.txt -Raw).Trim()
python -m tools.analyze_bond_position_v1_3 $sid
python -m tools.analyze_bond_coordinate_v1_6 $sid
```
For F4 substitute TARGET_F4. **Created is not MARKED.** Current capture is read-only and no automatic RAM writes are introduced.

## Per-run machine-readable audit
`tools/analyze_bond_coordinate_v1_6.py` produces `output/csv/bond_position_v1_3_<sid>_coordinate_v1_6.json`. Operator geometry/heading notes are kept in separate run manifest (`docs/BOND_COORDINATE_V1_6_RUN_TEMPLATE.json`). The script measures coordinate changes, other-field stability, exact post-change checkpoints, and whether a unique change occurs between WRITE_PRE and WRITE_APPLIED, but it *cannot know Bond's heading, physical world geometry, collision, or camera motion*.

## Comparison and acceptance
- For a **global-coordinate** claim, show that the **same signed target coordinate delta** changes world location consistently (same displacement vector in fixed-world frame), while the observed camera-relative movement may rotate/reverse as Bond faces other headings. Compare matched landmarks or an independently calibrated map.
- For a **Bond-relative coordinate** claim, demonstrate that displacement in a fixed-world frame rotates with Bond's independently verified heading, with comparable magnitude at 90/180 degree turns, no confounding camera offset/collision.
- When direction is only described as 'on-screen', **inconclusive**. No scripted inference of global vs local axes without a measurable world reference.
- Check for hidden coordinate recalc or snap-back and dynamic addresses across restarted sessions.
- Maintain both EC and F4 in experimental candidate state until replicated; no `catalog/symbols.json` promotion.

## Next operator action
Start with a heading-0 EC trial and a 180-degree-heading EC trial, both from the same world start and with matched signed small edit. Record static landmarks, camera behavior and numeric bytes. Then repeat with F4. This pair provides the fastest discriminating evidence before expanding the complete matrix.
