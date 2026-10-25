# Bond–Soldier v1.8.3 — Soldier Positive Motion Control

This is an experimental read-only control, NOT a confirmation of XYZ coordinates.

## Why
Previous session 20261025T144903Z_62005: 9,892 complete frames; 640 changes limited to bond_ec (183), bond_f0 (263), bond_f4 (194), only while the operator rotated Bond's view without walking. Soldier #1 raw candidates stayed constant. We need a positive test: make the same soldier **visibly move** and check whether its candidate bytes follow.

## Addresses
Bond 0x0D33E8, 0x0D33EC, 0x0D33F0, 0x0D33F4; soldier #1 0x20F594, 0x20F5AC. Experimental raw 4-byte snapshots. Do not assume the soldier watch `w u` is float32 or that fields are X/Z. KSEG0/KSEG1 alias equality is checked.

## Procedure
1. Stop previous collectors. `git pull --ff-only origin main`; create output/csv, output/commands, output/sessions. Load **bond_soldier_positive_motion_v1_8_3.lua** in BizHawk Lua Console with a reproducible savestate and one identified guard.
2. Send `python -m tools.send_bond_soldier_v1_8_3 BASELINE`. Wait for `MARKED`, hold for >=120 frames. Observe same soldier identity and stationary Bond/camera.
3. Enable Freeze manually. Confirm the soldier visibly stationary. Send `FREEZE_ON`, hold >=120 frames. Send `SOLDIER_STILL` and hold >=120 frames without changing Bond or camera.
4. Disable Freeze manually; confirm state and send `FREEZE_OFF`. When the **same** soldier visibly walks, send `SOLDIER_MOVING` and observe >=120 frames. If the guard will not move, label inconclusive and do not claim a positive control.
5. Re-enable Freeze manually when soldier is stopped and send `SOLDIER_REFROZEN`; hold >=120 frames. Send `STOP`; verify `DONE stop` before analyzing.
6. `$sid=(Get-Content .\output\sessions\bond_soldier_v1_8_3_session.txt -Raw).Trim()`; `python -m tools.analyze_bond_soldier_v1_8_3 $sid`; inspect `positive_control`, `phase_stats`, markers, missing frames, gaps, aliases.

Markers tag phases, do not operate cheats. Wait for each MARKED before the next command. The sender creates sequential absolute-path command files. Do not load savestates or reset while collecting. Camera-only may be separately tested in a new session. Reports never overwrite previous reports.

## Interpretation
Only call this a *candidate motion response* if the logger cleanly stops, positive phase coverage exists, candidate words change during SOLDIER_MOVING, and remain stable in Freeze/still controls. This is not evidence that they are coordinates without independent visual identity, movement timing, camera-negative controls, and repeat sessions. In particular, stale/constant values can indicate a wrong soldier structure. Never promote unverified offsets to GoldenEye.mapping.
