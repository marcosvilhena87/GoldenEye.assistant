# Bond Heading v1.9.7.1 — Corrected Controller Mapping

This version supersedes the **experimental control interpretation** in v1.9.7. The previous version remains available for provenance, but its C-button phase interpretation was wrong.

Operator-observed controls:
- `C_LEFT` / `C_RIGHT`: left/right **strafe**, not camera/body yaw.
- `C_UP` / `C_DOWN`: raise/lower **weapon arm**, not independently validated camera pitch.
- `R + analog`: move reticle independently on screen (test vertical and horizontal).
- Auto-Aim can adjust weapon aiming without asserting camera/body rotation.
- Physical turning is assigned separate `BODY_TURN_LEFT` / `BODY_TURN_RIGHT` markers, requiring the operator to use an **actually confirmed** yaw control.

## Implementation

`bond_heading_hud_v1_9_7_1.lua` is read-only to RDRAM and controller, logs raw candidate direction fields `0x0D33F8 / 0x0D3400`, plus auxiliary raw probes `0x0D3998 / 0x0D3D40 / 0x0D39A0 / 0x0D3D48`. Session output files are `output/csv/bond_heading_hud_v1_9_7_1_<sid>_{samples,events,termination}.csv`.

`tools/audit_bond_heading_hud_v1_9_7_1.py` preserves repeated phase occurrences, and separates **turn**, **strafe**, **weapon vertical**, and **manual reticle** experiments.

## Start

```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_7_1 -v
```

Load `bond_heading_hud_v1_9_7_1.lua` from the repository root in BizHawk Lua Console. Use `python -m tools.send_bond_heading_hud_v1_9_7_1 LABEL` one command at a time. Wait for Lua Console `ACK` before performing action. Hold still 120+ frames in HOLD phases. No Freeze, no RAM writes, no controller automation.

Recommended ordered sequence:

```text
REFERENCE
BASELINE_STILL
STRAFE_LEFT
HOLD_STRAFE_LEFT
STRAFE_RIGHT
HOLD_STRAFE_RIGHT
WEAPON_RAISE
HOLD_WEAPON_RAISE
WEAPON_LOWER
HOLD_WEAPON_LOWER
BODY_TURN_LEFT
HOLD_BODY_LEFT
BODY_TURN_RIGHT
HOLD_BODY_RIGHT
R_STICK_LEFT
HOLD_R_LEFT
R_STICK_RIGHT
HOLD_R_RIGHT
R_STICK_UP
HOLD_R_UP
R_STICK_DOWN
HOLD_R_DOWN
AUTOAIM_TARGET
HOLD_AUTOAIM
WEAPON_CHANGE
HOLD_WEAPON
MOVE_FORWARD_NO_TURN
HOLD_MOVE
LANDMARK_MATCH
HOLD_LANDMARK
STOP
```

Skip Auto-Aim if no target is available; for BODY_TURN phases use only the verified yaw input, otherwise **skip** instead of mislabeling strafe. Respect frame order when labeling experiments. Each ACK is a phase marker, **not** proof the intervention actually occurred.

## Audit

```powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_7_1_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_7_1 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_7_1_${sid}_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.control_comparison | Format-Table -AutoSize
$r.segments | Select-Object index,phase,frames,cumulative_steps_deg,net_modulo_deg,aux_changes | Format-Table -AutoSize
```

**Interpretation:** the heading candidate should remain stable in strafe and pure weapon elevation, but change during actual yaw. Reticle-only phases may affect different RAM fields. Correlation is not semantic proof; independent scene landmarks and second sessions are still needed. No changes to canonical GoldenEye.mapping.
