# Horizontal Correction v1.5 — Camera/Aim Separation

Read-only probe. The v1.4 candidate windows 0x0D3995 and 0x0D3D3D reacted to both target tracking and Bond/camera rotation; neither is a validated correction or camera heading.

Files: horizontal_correction_discovery_v1_5.lua; tools/send_horizontal_v1_5.py; tools/analyze_horizontal_v1_5.py; tests/test_horizontal_correction_discovery_v1_5.py.

Configuration: after verifying the RDRAM domain in BizHawk, set DOMAIN="RDRAM" and EXPECTED_SIZE=8388608. CAMERA_HEADING_ADDRESS is nil until independently validated. Do not guess an address.

Eight observed raw windows per frame: both original offsets and neighboring aligned offsets. Capture BEGIN and END for each action, always waiting for a Lua 'marked' acknowledgment:
- FIXED_NO_TARGET: stationary, no target.
- FIXED_AIM_LEFT, FIXED_AIM_RIGHT, FIXED_AIM_CENTER: stationary Bond/camera, aim-assisted gun visibly tracks enemy in respective directions.
- TURN_LEFT_NO_TARGET, TURN_RIGHT_NO_TARGET: Bond rotates, no eligible target.
- TURN_LEFT_AIM_OFF, TURN_RIGHT_AIM_OFF: rotate Bond with Auto-Aim OFF.
- REST_AFTER_TURN: camera stopped, test stable baseline.

Record operator observations of gun movement, enemy direction, and camera stability separately. Never infer a movement solely from the marker label. Keep same weapon and comparable geometry and avoid savestate changes within trials.

Start Lua, then verify a *new* session in output/sessions/horizontal_v1_5_session.txt. Send using, for example:
```powershell
python .\tools\send_horizontal_v1_5.py BEGIN_FIXED_NO_TARGET
# Verify '[horizontal.v1.5] marked BEGIN_FIXED_NO_TARGET' before intervention.
python .\tools\send_horizontal_v1_5.py END_FIXED_NO_TARGET
# Verify marked END before further work.
```
After completed interventions use STOP, confirm Lua processed it, then:
```powershell
$session = (Get-Content .\output\sessions\horizontal_v1_5_session.txt -Raw).Trim()
python .\tools\analyze_horizontal_v1_5.py $session
Import-Csv ".\output\csv\horizontal_v1_5_${session}_calibration_audit.csv" | Format-Table action,offset_hex,changes,operator_camera_condition -AutoSize
Import-Csv ".\output\csv\horizontal_v1_5_${session}_termination.csv" | Format-Table
```
Analyzer is immutable and should run only after session completion. Session collector limit: 36,000 iterations; split experiments across sessions if needed.

The analyzer validates contiguous frames; summarizes event counts, hypothetical float32 LE values, and timing. Camera conditions are **operator-declared**, not measured independently. Zero event lag does not show causality. Angular units, heading, aim correction, and data types are unvalidated. Do not write RAM, auto-rotate, auto-fire, or promote offsets to canonical mapping until independent signals and repeatability are established.
