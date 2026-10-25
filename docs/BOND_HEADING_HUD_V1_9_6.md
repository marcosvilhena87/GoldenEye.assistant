# Bond Heading v1.9.6 — Physical Heading Validation & Cross-Session Reproducibility

## Why
v1.9.5 SID \`20261025T202222Z_257815\` captured 9,265 valid frames and 6 ACKs with complete integrity. Measured cumulative headings at target phase ends were approximately 91°, 182°, 280°, 360.5°. The sensor appears numerically coherent, but its **physical meaning** is unknown. This version adds operator-labeled controls and retrospective/cross-session analysis. Neither the labels nor a constant vector alone establishes Bond's physical facing.

## Components
- \`bond_heading_hud_v1_9_6.lua\`: v1.9.5 live HUD plus \`phase\` column in per-frame CSV; RDRAM reads only, no game/controller writes.
- \`tools/send_bond_heading_hud_v1_9_6.py\`: same commands plus experimental phase markers, one command at a time.
- \`tools/audit_bond_heading_hud_v1_9_6.py\`: integrity, phase angular step direction/sum, hold stability and cross-session metrics.
- \`tests/test_bond_heading_hud_v1_9_6.py\`: synthetic test.
- Files created (new SID): \`_samples.csv\`, \`_events.csv\`, \`_termination.csv\`; \`_audit.json\` generated offline.

## Run
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_6 -v
\`\`\`
Start \`bond_heading_hud_v1_9_6.lua\` in BizHawk Lua Console from repository root; 8MiB RDRAM expected.

## Physical-controls protocol
Choose a visible fixed landmark; keep location unchanged except in MOVE phase. After each manual command, **wait for ACK** before performing that action. Hold still ~120+ frames for still/hold phases, with the operator visually verifying what occurred.

1. \`REFERENCE\`: local mathematical zero.
2. \`BASELINE_STILL\`: no controls.
3. \`BODY_TURN_LEFT\`: manual rotation left without walking; stop.
4. \`HOLD_AFTER_TURN\`: still.
5. \`BODY_TURN_RIGHT\`: manual opposite turn.
6. \`HOLD_AFTER_TURN\`: still. This marker may occur twice.
7. \`MOVE_FORWARD_NO_TURN\`: walk forward; do not turn.
8. \`HOLD_AFTER_MOVE\`: still.
9. \`AIM_ONLY\`: manipulate aiming control **without intending to change Bond's facing**. If the game couples actions, record the limitation; do not assume independence.
10. \`HOLD_AFTER_AIM\`: still.
11. \`WEAPON_CHANGE\`: change weapon without intentional turn.
12. \`HOLD_AFTER_WEAPON\`: still.
13. \`CAMERA_ONLY\`: only if an independent camera manipulation exists. Otherwise **skip** and note not testable; don't mislabel Bond rotation as camera-only.
14. \`HOLD_AFTER_CAMERA\`: if camera-only was possible.
15. \`LANDMARK_MATCH\`: return visually to an earlier reference.
16. \`HOLD_LANDMARK\`: still.
17. \`STOP\`: ensure script terminates.

Send commands as \`python -m tools.send_bond_heading_hud_v1_9_6 LABEL\`. The sender labels are **observational**, not executable input. No input automation or Freeze.

## Analyze
\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_6_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_6 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_6_\${sid}_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.phase_stats | Format-List
$r.hold_differences | Format-Table -AutoSize
\`\`\`
For two completed captures:
\`\`\`powershell
python -m tools.audit_bond_heading_hud_v1_9_6 <sid1> <sid2>
\`\`\`
Use actual SID literals instead of angle brackets.

## Validation gates
1. Complete capture, valid vector, no discontinuity, command ACK integrity.
2. Turning reversibility and operator-confirmed physical landmark agreement.
3. No change during pure translation or pure weapon switching.
4. Independently verified aiming/camera/body control separation.
5. Multiple sessions under documented ROM identity, N64 core and memory layout.
6. Mapping status remains **candidate**, not canonical validated heading, until these gates pass.
