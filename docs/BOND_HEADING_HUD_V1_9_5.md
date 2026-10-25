# Bond Heading v1.9.5 — Auditable Live Calibration Logging

This extends the operational v1.9.4 HUD with **RDRAM read-only** per-frame logging. It never writes game RAM or manipulates controllers.

## Inputs
- RDRAM (8 MiB), float32 big-endian X at \`0x0D33F8\`, Y at \`0x0D3400\`.
- Experimental \`atan2(y,x)\` reconstructed with portable atan quadrants for BizHawk NLua.
- Norm validity \`abs(x*x+y*y-1)<0.02\`.
- Manual visual controls still required to determine whether these fields represent Bond physical facing, camera, or weapon.

## Setup

\`\`\`powershell
cd "C:\Minha_Pasta\Jogos\BizHawk-2.11.1-win-x64\Lua\N64\GoldenEye.assistant"
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_5 -v
\`\`\`

Load \`bond_heading_hud_v1_9_5.lua\` from the repository root in the BizHawk Lua Console, with \`output/csv\`, \`output/sessions\`, \`output/commands\` directories present.

The session ID is written to \`output/sessions/bond_heading_hud_v1_9_5_session.txt\`.

Each session creates unique files:

- \`output/csv/bond_heading_hud_v1_9_5_<sid>_samples.csv\` — each observed frame: raw vector components, decoded values, norm, validity, angle, reference, relative angle, target, instantaneous error, accumulated turn, cumulative remaining, angular step, and reset reason.
- \`output/csv/bond_heading_hud_v1_9_5_<sid>_events.csv\` — REFERENCE and TARGET command ACKs, frame and sequence; records the reference angle, **not** an instantaneous measurement.
- \`output/csv/bond_heading_hud_v1_9_5_<sid>_termination.csv\` — explicit STOP reason and frame.

Files are never overwritten. Samples flush every 30 frames; command ACK events flush immediately. STOP closes all three.

## Operator protocol
Send one command at a time; await the corresponding \`ACK\` in the Lua Console before the next command.

\`\`\`powershell
python -m tools.send_bond_heading_hud_v1_9_5 REFERENCE
python -m tools.send_bond_heading_hud_v1_9_5 TARGET_90
python -m tools.send_bond_heading_hud_v1_9_5 TARGET_180
python -m tools.send_bond_heading_hud_v1_9_5 TARGET_270
python -m tools.send_bond_heading_hud_v1_9_5 TARGET_360
python -m tools.send_bond_heading_hud_v1_9_5 TARGET_0
python -m tools.send_bond_heading_hud_v1_9_5 STOP
\`\`\`

After REFERENCE, keep Bond still and note the visual landmark. For each TARGET, rotate **manually**, slow near the target, and pause for 120+ frames. Positive target convention is mathematical: earlier left turns produced negative increments. For a full circle, use **cumulative** metric, not modulo error. Do not use Freeze or load savestates mid-session.

## Offline audit

\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_5_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_5 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_5_\${sid}_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.command_checkpoints | Format-Table -AutoSize
$r.target_intervals | Format-Table -AutoSize
$r.reset_counts
\`\`\`

Audit checks contiguous frames, duplicate frames, event ordering, ACK sequence and explicit STOP. It reports the minimum absolute modulo error and ending error during each target phase, plus cumulative angle and reset counts. It **does not** infer that a target was achieved from the ACK alone. No canonical heading validation or GoldenEye.mapping promotion until independently tested against scene landmarks and physical directions in multiple sessions.

Compatibility note: NLua lacks \`math.ldexp\` and \`math.atan2\`; v1.9.5 uses portable arithmetic and a quadrant-correct atan helper.
