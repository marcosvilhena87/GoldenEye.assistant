# Freeze Transition Timing & Soldier Coordinate Validation v1.8.4

## Scope
Read-only per-frame logger plus offline episode detector. **This version does not validate world XYZ or the freeze indicator.** Build on v1.8.3 session `20261025T151226Z_143169`: `SOLDIER_STILL` showed motion-like changes during frames 146000–146064 and 146243–146323; the gap alone cannot prove a freeze state.

## Inputs
Candidate Bond: 0x0D33E8, 0x0D33EC, 0x0D33F0, 0x0D33F4 (four-byte raw); candidate soldier: 0x20F594, 0x20F5AC (four-byte raw with *provisional* float view); provisional freeze indicator: **0x02C90C (u8)**. Reads KSEG0/KSEG1 System Bus only. No memory writes or cheat toggling.

## Live protocol (BizHawk)
1. Create output/csv, output/sessions, output/commands; load `bond_soldier_freeze_transition_v1_8_4.lua`. Record SID from console.
2. Keep Bond/camera fixed and track an identifiable soldier. Send `python -m tools.send_bond_soldier_v1_8_4 BASELINE`; collect at least 120 frames.
3. Freeze ON manually; send `FREEZE_REQUEST_ON` immediately when toggling and `FREEZE_ON` only after visual confirmation, waiting for each `MARKED`. Collect 120+ frames. Send `SOLDIER_STILL`, keep still 120+ frames.
4. Freeze OFF manually; send `FREEZE_REQUEST_OFF`, then `FREEZE_OFF`; when soldier visibly moves send `VISUAL_MOVING` then `SOLDIER_MOVING`. Observe >=120 frames, no Bond movement.
5. Freeze ON again; send `FREEZE_REQUEST_ON` after toggling and `SOLDIER_REFROZEN` after visually stopped; observe at least 120 frames; mark `VISUAL_STILL` if useful (do not mark before stationarity).
6. Send `STOP` and wait `DONE stop`. Never restore savestate while logging. Labels are annotations only, not automatic actions. Record visual observations separately with actual frame numbers.
7. `$sid=(Get-Content .\output\sessions\bond_soldier_v1_8_4_session.txt -Raw).Trim()`; `python -m tools.analyze_bond_soldier_v1_8_4 $sid`.

## Analysis
`--max-quiet 12` means events separated by more than 12 frames start distinct episodes. `--settle-frames 120` requires a contiguous quiet window within the marker phase. Reports include frame ranges of episodes, provisional indicator transitions, and last-change-to-quiet delays. Phase markers bound measurements; exact cheat activation time is *not* inferred. A phase with many noisy changes and a short quiet window remains inconclusive.

## Validation gates
Observing the same identifiable guard changing raw candidate fields in movement phases and stabilizing after Freeze is a **motion-associated candidate**, not proof of coordinates. Require freeze on/off visual evidence, positive/negative controls, stable identity, camera-only control, independently measured geometry, repeated sessions and exact ROM/core metadata before considering canonical mapping. No automatic promotion into GoldenEye.mapping.
