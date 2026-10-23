# Horizontal Correction Discovery v1.3 — Camera/Aim Discrimination

**Two different movements:** native Auto-Aim may redirect the weapon aim **without moving Bond's camera**. Manually turning Bond moves the camera. A field responding to both cannot be identified as pure Auto-Aim correction without stronger controls.

This version records the same two *unvalidated*, unaligned four-byte RDRAM windows as v1.2: `0x0D3995` and `0x0D3D3D`. It does not know or assert any camera/heading address. Camera fixation is an **operator declaration**, not a measurement.

## Procedure

1. Update repository and run tests. Verify `memory.getmemorydomainsize("RDRAM")==8388608` in BizHawk; set `DOMAIN="RDRAM"` and `EXPECTED_SIZE=8388608` inside `horizontal_correction_discovery_v1_3.lua`. Launch collector, note the new session ID.
2. Each condition uses `BEGIN_ACTION`, **wait for exact Lua marked BEGIN**, carry out the intervention, `END_ACTION`, and wait for exact Lua marked END. Check markers CSV each time.
3. Recommended order, each in a new controlled scene as appropriate:
   - `FIXED_CAMERA_CONTROL`: Bond and camera fixed; single static environment, do nothing.
   - `FIXED_CAMERA_ON_TARGET`: Auto-Aim ON, Bond/camera fixed, move one eligible enemy across sightline (or move its position via normal gameplay only), do not manually aim or turn Bond.
   - `FIXED_CAMERA_OFF_TARGET`: same test with Auto-Aim OFF and closely comparable geometry.
   - `FIXED_CAMERA_NO_TARGET`: Auto-Aim ON, camera fixed, no eligible enemy.
   - `TURN_CAMERA_NO_TARGET`: no eligible enemy, manually rotate Bond/camera left or right.
4. If unable to keep camera fixed or the target/comparability differs, note the invalid trial; do not call it a validated control. Avoid save/load or emulator reset mid-session because frame counters can jump. Collector caps at 36,000 frames; start a new session for additional work.
5. `STOP` only outside a bracket.

Example PowerShell:
```powershell
python .\tools\send_horizontal_v1_3.py BEGIN_FIXED_CAMERA_CONTROL
# confirm '[horizontal.v1.3] marked BEGIN_FIXED_CAMERA_CONTROL ...'
python .\tools\send_horizontal_v1_3.py END_FIXED_CAMERA_CONTROL
# confirm END; proceed to next action
```

After confirmed complete windows:
```powershell
python .\tools\analyze_horizontal_v1_3.py SESSION_ID
Import-Csv .\output\csv\horizontal_v1_3_SESSION_ID_camera_aim_audit.csv | Format-Table action,offset_hex,changes,unique_values,first_float32_le,last_float32_le -AutoSize
```

Reports are immutable and descriptive. A derived float32 number is not an identified angle; temporal response could be target position, animation or camera effects. There is **no** writing, movement automation, automatic firing or promotion to `GoldenEye.mapping/catalog/symbols.json`. Future camera-heading discovery is a separate track with no inferred addresses.
