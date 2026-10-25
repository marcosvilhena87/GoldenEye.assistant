# Bond Heading v1.9.7 — Camera, Body & Weapon Aim Separation

## Goal
Run an intervention-driven comparison of:
- Horizontal C-Buttons: operator-observed turn, central reticle.
- Vertical C-Buttons: operator-observed vertical camera view.
- R + analog stick: move the gun reticle horizontally and vertically independently on screen.
- Auto-Aim with a visible target: observe gun aim adjustment **without assuming** camera rotation.
- Negative controls: stillness, weapon change and forward translation without turning.

These are *observed controller behaviors* reported by the operator, not conclusions already proven from RDRAM. The pair \`0x0D33F8/0x0D3400\` remains the **candidate** unit direction vector. The aux fields \`0x0D3998/0x0D3D40/0x0D39A0/0x0D3D48\` are raw investigative probes with **no** weapon-aim semantics asserted.

## Files
- \`bond_heading_hud_v1_9_7.lua\`: graphical read-only heading HUD and per-frame CSV including four raw aux fields and phase.
- \`tools/send_bond_heading_hud_v1_9_7.py\`: phase command sender.
- \`tools/audit_bond_heading_hud_v1_9_7.py\`: group contiguous phase **occurrences** (does not collapse repeats), verify ACK/frame integrity, compare vector angle changes and raw aux activity.
- \`tests/test_bond_heading_hud_v1_9_7.py\`: synthetic unit tests.

## Setup
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_7 -v
\`\`\`
Start \`bond_heading_hud_v1_9_7.lua\` in BizHawk Lua Console with repository root as CWD. Requires RDRAM 8 MiB; READ ONLY (never freezes/writes memory or sends controller inputs). The experiment creates new session-specific \`_samples.csv\`, \`_events.csv\`, \`_termination.csv\` under \`output/csv\`.

## Manual experimental sequence
Use \`python -m tools.send_bond_heading_hud_v1_9_7 <LABEL>\`, **one at a time**, wait for \`ACK\` in Lua Console, then perform that action in-game, then send the next HOLD/phase marker. Keep still for at least 120 frames in HOLD phases.

1. \`REFERENCE\` — reference orientation while Bond is still.
2. \`BASELINE_STILL\` — do nothing.
3. \`C_LEFT\` — turn left using only horizontal C-Button; \`HOLD_C_LEFT\`.
4. \`C_RIGHT\` — turn right using only horizontal C-Button; \`HOLD_C_RIGHT\`.
5. \`C_UP\` — vertical camera view up using only C-Button; \`HOLD_C_UP\`.
6. \`C_DOWN\` — view down using only C-Button; \`HOLD_C_DOWN\`.
7. \`R_STICK_LEFT\` — hold R + analog left, *verify reticle* moves but Bond stays still; \`HOLD_R_LEFT\`.
8. \`R_STICK_RIGHT\` — same to right; \`HOLD_R_RIGHT\`.
9. \`R_STICK_UP\` — R + analog up; \`HOLD_R_UP\`.
10. \`R_STICK_DOWN\` — R + analog down; \`HOLD_R_DOWN\`.
11. \`AUTOAIM_TARGET\` — visible enemy, Auto-Aim active, operator should verify gun auto-alignment *without* manual Bond rotation; \`HOLD_AUTOAIM\`. If no target, skip this pair.
12. \`WEAPON_CHANGE\` — weapon switch without turning; \`HOLD_WEAPON\`.
13. \`MOVE_FORWARD_NO_TURN\` — forward motion without rotating; \`HOLD_MOVE\`.
14. \`LANDMARK_MATCH\` — return to known fixed visual landmark direction; \`HOLD_LANDMARK\`.
15. \`STOP\`.

**Caution:** if vertical C-Buttons actually change pitch rather than move a physically separate camera, report this without forcing a body/camera distinction. Similarly the R+stick and Auto-Aim actions may couple aim and body in game modes: visually verify actions; command labels are not proof.

## Audit
\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_7_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_7 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_7_\${sid}_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.control_comparison | Format-Table -AutoSize
$r.segments | Select-Object index,phase,frames,cumulative_steps_deg,net_modulo_deg,aux_changes | Format-Table -AutoSize
\`\`\`
Metrics are phase **correlations** only. A candidate independent gun-aim source requires a field changing during reticle movement and Auto-Aim but not simple body turn; any confirmation needs a new directed neighborhood search and multiple sessions. Neither body nor camera physical heading is validated by this collector, and no canonical GoldenEye.mapping promotion is authorized.
