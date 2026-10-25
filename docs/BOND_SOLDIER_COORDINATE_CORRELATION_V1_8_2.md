# Bond–Soldier Coordinate Correlation v1.8.2

## Status and scope
Experimental READ ONLY acquisition and offline correlation. Addresses are **not canonical**. Bond candidate float32 BE: `0x0D33EC`, `0x0D33F4`; controls `0x0D33E8`, `0x0D33F0`. Soldier #1 **unverified candidates** `0x20F594`, `0x20F5AC`. Both soldier offsets are logged as 4 raw bytes and a tentative float32 BE interpretation; the original RAM Watch `w u` display does **not** prove 32-bit float32 type, so use raw bytes as primary evidence.

## Prerequisites
Use BizHawk 2.11.1 N64 with System Bus, the same verified ROM/core, a reproducible savestate, and manually identified Soldier #1. Compare with GoldenEye.mapping before promoting any symbol. No cheats are activated automatically; do not write to Soldier #1.

## Capture
1. Create `output/csv`, `output/commands`, `output/sessions`; load `bond_soldier_coordinate_correlation_v1_8_2.lua` in Lua Console. It prints a unique SID and starts per-frame read-only capture.
2. To enqueue a marker, create a *new* UTF-8 text file named `output/commands/bond_soldier_v1_8_2_<SID>_0001.txt`, containing `LABEL:BASELINE`. Wait for `MARKED BASELINE` in Lua Console before sending `0002`. Subsequent labels: `FREEZE_ON`, `FREEZE_OFF`, `CAMERA_ONLY`, `BOND_MOVE`, `SOLDIER_MOVE`, `WRITE_PRE`, `WRITE_APPLIED`, `WRITE_OBSERVE`, `STOP`. Each file has **only one line**. See example helper below.
3. Capture at least 120 stable frames of baseline with both actors motionless; verify soldier identity and freeze with ON/OFF visual controls. Turn camera while Bond and soldier remain stationary (CAMERA_ONLY). Check whether candidate bytes move, which would suggest view-dependent buffers.
4. For an EC intervention, record WRITE_PRE after stationary baseline. Change only the **verified complete 32-bit target** by a small reversible amount manually (never via this logger). Record the raw before/after and whether Bond visibly moves. Then WRITE_APPLIED; marker delay is expected and not used to infer actual intervention frame. Hold still for at least 120 frames; WRITE_OBSERVE. STOP and verify DONE stop.
5. Save raw CSV and report. Restore the pristine savestate **after stopping** and run separate F4 and no-write control sessions. Do not reuse a stopped SID.

## PowerShell example
```powershell
$sid = (Get-Content .\output\sessions\bond_soldier_v1_8_2_session.txt -Raw).Trim()
$stem = "bond_soldier_v1_8_2_$sid"
# For each marker in order, increment sequence and WAIT for MARKED before continuing:
[System.IO.File]::WriteAllText("output/commands/${stem}_0001.txt", "LABEL:BASELINE`n")
# ... observe in BizHawk, then create 0002, 0003, etc.
python -m tools.analyze_bond_soldier_v1_8_2 $sid
```

## Interpretation gates
The analyzer reports raw changes, phases, aliases, continuity, and whether both soldier candidate words stay unchanged at Bond transitions and for 120 subsequent frames. It deliberately never validates physical position or global axes. Raw stability is **not** proof of independent spatial measurement. A relative coordinate claim additionally requires externally validated actor identity, same physical coordinate system, camera-negative controls, soldier-motion positive control, freeze ON/OFF and repeated independent sessions.

## Prior EC session
Session `20261025T143428Z_10967`: `0x0D33EC` changed at frame 18133, raw `469DCB48` -> `469CCB48`, float32 BE -128, while the other three Bond words were stable in the inspected window. WRITE_APPLIED was frame 18712, 579 frames later. That v1.3 capture did **not** collect soldier candidate words and cannot prove soldier/Bond correlation; it cannot be retroactively enriched.

## Safety
System Bus is read with `memory.read_u8` only. KSEG0/KSEG1 aliases are checked; no RAM writes are made. No address is promoted to validated GoldenEye.mapping symbols automatically.
