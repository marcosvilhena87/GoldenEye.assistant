# Bond Position Validation v1.4 — Reversibility & Orthogonal Write Controls

## Existing evidence (not a canonical symbol)
In the v1.3 EC capture, at frame 676296 the four raw bytes at 0x0D33EC changed `469857EF -> 469757EF`, interpreted as float32 BE `19499.9668 -> 19371.9668` (delta -128). The operator subsequently confirmed Bond moved *forward on screen*. Later samples recorded `469757EF` unchanged through marker-relative +120 frames. This supports a physical effect compatible with a manual u16 edit, but does not prove a global X/Z axis or actual write-to-frame persistence beyond operator annotation.

## Design: three isolated runs, no automatic writes
Use existing v1.3 observer, sender and analyzer. Each run starts from **the same clean savestate**, with Bond stationary, fixed heading and camera, away from walls. Quit the previous Lua capture with STOP **before restoring** the savestate, then restart the capture with a fresh session ID. Verify the current full 32-bit raw word in System Bus before entering anything in Cheat Search. `0D33EC` and `0D33F4` are 32-bit *candidates*, while the original Cheat Search edit was a 16-bit unsigned word. For F4 especially, **do not assume** the original u16 cheat address/representation is verified; confirm its full 4-byte match before touching memory. Prefer making a backup and avoiding extreme jumps or dangerous positions.

### Run A — EC negative displacement
1. Select `TARGET_EC`, mark BASELINE and WRITE_PRE. Read EC baseline (the old run used `469857EF`, **not** a guaranteed value on a new run).
2. In Cheat Search, edit only the verified upper u16 part, a small reproducible decrement; for an exact reproducibility check only if the full baseline remains `469857EF`, `4698 -> 4697` would give `469757EF`, delta -128.
3. Confirm Bond's movement visually and its world position relative to fixed geometry. Mark WRITE_APPLIED, observe >=120 emulated frames without controls, mark WRITE_OBSERVE, STOP and analyze.

### Run B — EC positive displacement
Restore identical savestate **after finishing Run A**. Same heading, same initial EC bytes. Use a small positive increment (if original bytes really are `469857EF`, `4698 -> 4699` yields `469957EF`; numeric delta is **not guaranteed +128** since float32 spacing and bit changes depend on raw value). Record the actual numerical difference. Check for displacement in the opposite direction. Complete identical 120-frame observation and STOP.

### Run C — F4 independence
Restore original savestate once more, start a fresh capture, select `TARGET_F4`. Record complete F4 raw 32-bit baseline. Only after confirming the Cheat Search domain, width, and full four-byte interpretation, make one *small reversible* single-field manual change. Do not change EC. Record whether Bond displaced perpendicular to Runs A/B, including visual landmarks/camera. STOP and analyze.

### Per-run commands
```powershell
python -m tools.send_bond_position_v1_3 TARGET_EC
python -m tools.send_bond_position_v1_3 BASELINE
python -m tools.send_bond_position_v1_3 WRITE_PRE
# perform exactly one manual Cheat Search edit after WRITE_PRE is marked
python -m tools.send_bond_position_v1_3 WRITE_APPLIED
# let emulator run >= 120 frames, then:
python -m tools.send_bond_position_v1_3 WRITE_OBSERVE
python -m tools.send_bond_position_v1_3 STOP
$sid=(Get-Content .\output\sessions\bond_position_v1_3_session.txt -Raw).Trim()
python -m tools.analyze_bond_position_v1_3 $sid
```
For Run C use `TARGET_F4` instead. **Never paste/run all sender commands in a batch**; await MARKED before each intervention or next phase. Note frame of actual first changed byte from `_events.csv`, not just WRITE_APPLIED marker.

## Operator evidence table (fill independently for each run)
Record session ID, loaded ROM/core identity if available, savestate ID, initial heading and fixed visual reference, target, Cheat Search address/domain/width, 4-byte before/after hex, actual first changed frame, observed direction and camera response, numeric float32 delta, 1/30/120-frame raw values counted relative to actual change, whether Bond remains at new geometry, and any collision.

## Pass/fail criteria
- **Memory effect:** full raw bytes differ at a documented intervention; KSEG0 and KSEG1 agree.
- **Memory persistence:** raw post-write bytes stay unchanged at exact 1/30/120 frames after *first actual changed frame*, with no input and no further edits.
- **Physical causality:** two independent EC interventions from identical physical baseline produce repeatable, opposite visual displacements, with recorded camera observations.
- **Second axis:** isolated F4 write moves Bond in physically distinct direction, while EC stays constant, repeated in an independent session.
- **Canonical mapping:** do not promote until ROM/core match, absolute vs dynamic address, coordinate representation, positive/negative controls and independent replication are established.

Every criterion not supported by observations is `not_confirmed`, not inferred from marker names or numerical correlation. The code remains read-only and will never alter RAM automatically.
