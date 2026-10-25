# Bond Position Validation v1.5 — Second Axis Independence

Status: **protocol ready; no v1.5 F4 experimental result yet**. This is a read-only instrumented study, not a canonical mapping promotion.

## Prior experimental evidence
`0x0D33EC` was modified in three observed sessions with float32-BE deltas `-128, -128, +128`. The operator reported Bond moving forward, forward, backward, respectively. This establishes an **operator-observed bidirectional physical effect** for EC in those sessions, without proving axis names or universal address stability. See `GoldenEye.mapping/experiments/bond_position_reversibility_v1_4_20261024.json`.

## Hypothesis and controls
- Hypothesis H1: `0x0D33F4` is a second position component independently writable from `0x0D33EC`.
- Null H0: an F4 change does not induce an independent physical displacement, or EC changes at the same time.
- Negative control: Bond stationary, no controller input, no Cheat Search changes; check EC and F4 stability.
- Intervention: one verified, reversible **manual** edit of F4 only, preferably the upper u16 after confirming full 4-byte big-endian correspondence.
- Positive/reverse control: restart from the **same original savestate**, fixed heading/camera/landmarks and change F4 in the opposite direction in a second session.
- No pre-assigned F4 raw values or assumption that float32 change is exactly 128. Actual initial bytes dictate safe edits. Cheat Search domain/width must be verified separately for F4. Never re-use the EC u16 address as F4.

## Procedure — Run A: F4 write
1. Update repository. Create directories `output/csv`, `output/commands`, `output/sessions`. Prepare safe open area; disable existing cheats. Save a clean savestate, note level, ROM identity, BizHawk/N64 core, Bond heading and camera. **Stop any old Lua script before starting a new one**.
2. Run `bond_position_discovery_v1_3.lua` in BizHawk Lua Console (existing code samples EC, F4, E8, F0 each frame through System Bus aliases; does not write RAM). Confirm new `session=` line.
3. Send commands below **one by one**, waiting for `MARKED` in Lua Console before sending the next. After BASELINE, hold still for >=120 emulated frames.
4. After `WRITE_PRE` is marked, record 4-byte F4 and EC raw values; manually change **only** the verified F4 field by a small reversible amount. Observe motion relative to fixed landmarks and note camera motion; do not touch controls.
5. Send `WRITE_APPLIED`, allow >=120 frames with no further intervention, send `WRITE_OBSERVE`, then `STOP`; confirm `DONE stop`.
6. Analyze session. For an independent second direction, EC must stay constant across baseline/intervention/hold while F4 changes exactly once. Memory independence alone is not visual/physical independence.

```powershell
git pull --ff-only origin main
python -m tools.send_bond_position_v1_3 TARGET_F4
python -m tools.send_bond_position_v1_3 BASELINE
python -m tools.send_bond_position_v1_3 WRITE_PRE
# AFTER "MARKED WRITE_PRE": inspect EC/F4, then do one manual F4 edit
python -m tools.send_bond_position_v1_3 WRITE_APPLIED
# AFTER >=120 emulated frames:
python -m tools.send_bond_position_v1_3 WRITE_OBSERVE
python -m tools.send_bond_position_v1_3 STOP
$sid=(Get-Content .\output\sessions\bond_position_v1_3_session.txt -Raw).Trim()
python -m tools.analyze_bond_position_v1_3 $sid
python -m tools.analyze_bond_second_axis_v1_5 $sid
$r=Get-Content ".\output\csv\bond_position_v1_3_${sid}_second_axis_v1_5.json" -Raw | ConvertFrom-Json
$r | Select-Object session,marker_order_valid,isolated_f4_memory_change_with_stable_ec
$r.f4_change_candidates_in_intervention_window | ConvertTo-Json -Depth 8
```

**Do not execute all send commands at once**: the comments above denote physical operator actions and frame waits, not a batch script. v1.3 sender prints `Created`, which does **not** confirm BizHawk consumed a command. Wait for `MARKED`.

## Procedure — Run B: reverse F4 write
After Run A ends and before loading a savestate, ensure Lua says `DONE stop`. Restore the **same original savestate**, with the same Bond orientation and fixed scene landmarks. Run fresh v1.3 Lua, generate fresh session ID, repeat the sequence using opposite signed F4 change. Do not overwrite prior CSV/JSON. Expect opposite relative physical displacement if the candidate controls an independent component.

## Analyzer semantics
The v1.5 analyzer reads existing `bond_position_v1_3_<sid>_timeline.csv` and marker files. It writes *new* `_second_axis_v1_5.json` and never overwrites previous output. It locates actual first F4 change frames **between** WRITE_PRE and WRITE_APPLIED; requires exactly one, tests EC constancy from WRITE_PRE to change+120, exact post-change checkpoints +1/+30/+120, clean STOP, no discontinuities, correct marker order, and KSEG alias equality. If a change occurs after WRITE_APPLIED, outside this window, or checkpoints absent, the automatic isolation flag remains false and manual review is needed. It cannot observe geometry or prove the manual operation itself occurred.

## Acceptance criteria
1. **Read consistency:** System Bus KSEG0/KSEG1 words for EC/F4 agree (0 alias mismatches).
2. **Isolation:** one changed F4 value in the intervention window, EC unchanged throughout F4 write and 120 subsequent frames; no controller movements and no other cheats.
3. **Persistent write candidate:** F4 raw after-value is identical on change-relative +1/+30/+120 samples.
4. **Visual second-axis behavior:** camera/heading held fixed, Bond's movement compared against *fixed world landmarks* differs from prior EC forward/back, not solely on-screen direction.
5. **Reversibility:** opposite F4 edit from original savestate produces opposite geometric displacement; verify a second session.
6. **Canonical mapping:** remains forbidden until ROM/core mapping, pointer vs absolute address, independent replays and world-axis calibration.

## Operator data to retain
For each session: session ID, run A/B, original savestate label, ROM/core version, fixed heading, EC full hex before/after, F4 full hex before/after, manual Cheat Search address/domain/u16 or u32 width, change frame, screen/world landmark movement, camera movement, any collisions, and analyzer JSON result.

**Current mapping status:** F4 unconfirmed candidate; EC experimental bidirectional physical effect, not canonical. Neither is globally named X/Z.
