# Bond Heading v1.9.8 — Camera Pitch & Reticle Offset Discovery

## Corrected physical control model
- C-Left/Right: strafe, no intentional heading change.
- C-Up/Down: vertically tilt **camera**, with reticle hidden and centered.
- R + analog Up/Down: tilt **camera and visible freely moving reticle**; does not advance/back Bond.
- R + analog Left/Right: horizontal Bond/camera rotation **still active**.
- Auto-Aim: visual gun aim correction without assuming a camera response.

These are **operator observations**. The pitch address and reticle offsets are NOT established.

## Implementation
- \`bond_heading_hud_v1_9_8.lua\`: read-only 8 MiB RDRAM heading vector, 4 raw 32-bit aux probes and each auxiliary decoded as a possible big-endian float32, all recorded by frame/phase; no controller automation.
- \`tools/send_bond_heading_hud_v1_9_8.py\`: one-command-at-a-time operator phase markers.
- \`tools/audit_bond_heading_hud_v1_9_8.py\`: phase occurrence-preserving numeric range, raw change rate, and comparisons between normal camera pitch vs R-mode pitch.
- \`tests/test_bond_heading_hud_v1_9_8.py\`: synthetic tests.

## Run
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_8 -v
\`\`\`
Launch \`bond_heading_hud_v1_9_8.lua\` from repository root in BizHawk Lua Console. Each new session ID is stored at \`output/sessions/bond_heading_hud_v1_9_8_session.txt\`.

Send commands using \`python -m tools.send_bond_heading_hud_v1_9_8 LABEL\`. Wait for console ACK before each operator action. Keep the game still for at least 120 frames after each intervention.

## Suggested sequence
\`\`\`text
REFERENCE
BASELINE_STILL
CAMERA_PITCH_UP
HOLD_CAMERA_UP
CAMERA_PITCH_DOWN
HOLD_CAMERA_DOWN
AIM_MODE_PITCH_UP
HOLD_AIM_UP
AIM_MODE_PITCH_DOWN
HOLD_AIM_DOWN
AIM_MODE_YAW_LEFT
HOLD_AIM_LEFT
AIM_MODE_YAW_RIGHT
HOLD_AIM_RIGHT
BODY_TURN_LEFT
HOLD_BODY_LEFT
BODY_TURN_RIGHT
HOLD_BODY_RIGHT
STRAFE_LEFT
HOLD_STRAFE_LEFT
STRAFE_RIGHT
HOLD_STRAFE_RIGHT
AUTOAIM_STATIC
HOLD_AUTOAIM_STATIC
AUTOAIM_MOVING
HOLD_AUTOAIM_MOVING
WEAPON_CHANGE
HOLD_WEAPON
STOP
\`\`\`
For \`CAMERA_PITCH_*\`: release R, use C-Up or C-Down only. For \`AIM_MODE_PITCH_*\`: hold R and use analog vertical; visually verify on-screen reticle moves **and** camera pitch changes. For \`AIM_MODE_YAW_*\`: expect horizontal rotation, not an isolated reticle move. Do not force Auto-Aim segments when enemy/static/moving target unavailable. No memory writes, cheats, Freeze, controller injection or auto-alignment.

## Offline audit
\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_8_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_8 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_8_\${sid}_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.differential_raw_activity | Format-Table -AutoSize
$r.segments | Select-Object index,phase,frames,heading_cumulative_step_deg,fields | Format-Table -AutoSize
\`\`\`

The fields \`0x0D3998\`, \`0x0D3D40\`, \`0x0D39A0\`, \`0x0D3D48\` remain **auxiliary candidates only**. The float32 interpretation is diagnostic, not validated, and co-changing mirrored fields can represent derived transforms or animations. The audit does not claim actual reticle screen coordinates or independently separated camera/reticle contributions. A later controlled search and visual cursor alignment is necessary before promoting a mapping in GoldenEye.mapping.
