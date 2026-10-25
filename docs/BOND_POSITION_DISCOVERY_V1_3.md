# Bond Position Discovery v1.3 — Controlled Write Persistence & Coordinate Confirmation

The read-only probe targets candidate float32 big-endian words at 0D33EC and 0D33F4, preserving 0D33E8 and 0D33F0 as controls. Previous v1.2 showed opposite-sign changes with forward/back and strafe movement, and stable hold intervals, but no write intervention. Neither X/Z names nor physical position nor write persistence are established.

## Run

1. In repository root, `git pull --ff-only origin main`; create `output/csv`, `output/sessions`, `output/commands`.
2. Prepare a known safe gameplay state and save it before running Lua. Start `bond_position_discovery_v1_3.lua` in the BizHawk Lua Console.
3. In PowerShell, run `python -m tools.send_bond_position_v1_3 TARGET_EC` and wait for MARKED. Then send `BASELINE`, allowing at least 120 frames motionless.
4. Send `WRITE_PRE` and await MARKED; record the exact Cheat Search raw 32-bit value, scene location and camera behavior.
5. With a verified Cheat Search address and correct width, manually apply a SMALL REVERSIBLE change to the target only; do not use Lua writes. Note the exact before/after raw values and whether Bond visibly moved. Send `WRITE_APPLIED` immediately after the intervention and wait for MARKED.
6. Do not move Bond, rotate camera, or change cheats during the next 120+ frames. Send `WRITE_OBSERVE` after the hold, then `STOP`. Confirm `DONE stop`.
7. Run `$sid=(Get-Content .\output\sessions\bond_position_v1_3_session.txt -Raw).Trim()`; `python -m tools.analyze_bond_position_v1_3 $sid`.
8. Restore the original save state only after STOP; launch a **new** Lua session, selecting `TARGET_F4`, and repeat from identical physical conditions. Repeat both tests on a new game/session to assess address stability.

**Important:** `WRITE_APPLIED` is the first frame *after* the operator marker is consumed, not necessarily the first frame after the actual manual write. The analyzer reports frame 0/1/30/120 relative to that marker, and preserves raw bytes so the actual first changed frame can be audited. STOP before savestate loads: the logger intentionally terminates on timeline discontinuities.

## Files
`output/csv/bond_position_v1_3_<sid>_{timeline,markers,events,termination,discontinuities}.csv`, and `_analysis.json`. No autosave overwrites. All writes to memory are external, manually controlled. If Cheat Search uses a word-sized u16 representation, do NOT assume writing 16 bits constitutes setting an entire float32; first verify complete four-byte before/after representations.

## Evidence gate
Only claim **observed memory persistence** when stable raw bytes are seen at 1/30/120 after a documented intervention; even then, distinguish it from **physical coordinate confirmation**. Position requires external visual/geometry ground truth, negative camera control, and independent cross-session replication. Keep `GoldenEye.mapping` symbols unvalidated.
