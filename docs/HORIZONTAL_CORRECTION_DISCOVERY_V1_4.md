# Horizontal Correction Discovery v1.4 — Directional Calibration Protocol

Read-only temporal investigation, maintaining separation between **weapon aim correction** (potentially changing with camera fixed) and **Bond/camera heading** (changes when Bond rotates). Camera immobility and target position are **declared by the operator**, not measured by a validated camera symbol. No address is promoted; no RAM writes or automated input.

## Improvements over v1.3

- Two experimental 4-byte RDRAM windows: `0x0D3995`, `0x0D3D3D`, sampled once per emulated frame.
- Atomic, numbered `BEGIN_*`/`END_*` requests and explicit STOP.
- Immutable session-specific timeline, transitions, markers, and **termination CSV** containing `stop`, `frame_limit`, or `invalid_marker`; the Lua Console also prints FINISHED reason.
- Offline window analysis of transitions, unique values, hypothetical float32 LE first/last, simultaneous events, and paired nearest-event lag (8-frame matching threshold). Lag does **not** establish producer/consumer direction.
- Session-specific output; past v1–v1.3 evidence stays untouched.

## Procedure

In `horizontal_correction_discovery_v1_4.lua`, independently verify and set `DOMAIN="RDRAM"`, `EXPECTED_SIZE=8388608`. Start in BizHawk, note session, verify Lua is advancing frames. Capture one condition per completed bracket, **wait for each `marked` before acting**:

1. `BASELINE`: camera fixed, no moving eligible target.
2. `ON_TARGET_LEFT`: Auto-Aim ON, camera fixed, eligible target moves toward left.
3. `ON_TARGET_RIGHT`: ON, camera fixed, target moves toward right.
4. `ON_TARGET_CENTER`: ON, target crosses the central reticle.
5. `OFF_TARGET_LEFT`: OFF, comparable leftward target movement.
6. `OFF_TARGET_RIGHT`: OFF, comparable rightward movement.
7. `NO_TARGET`: ON, no eligible target, camera fixed.
8. `TURN_CAMERA_CONTROL`: no eligible target, manually turn Bond/camera.

Use `python .\tools\send_horizontal_v1_4.py BEGIN_BASELINE`, verify Lua `marked BEGIN_BASELINE`, do experiment, then `END_BASELINE`; repeat with other actions. Close all brackets; then `STOP`. If collecting all cases takes >36,000 frames, use several independent sessions rather than rushing or trusting commands that the collector has not consumed. Do not load savestate in an active session. Keep the same weapon, range and comparable geometry across trials as much as practical.

After captures and verified markers:
```powershell
python .\tools\analyze_horizontal_v1_4.py SESSION_ID
Import-Csv .\output\csv\horizontal_v1_4_SESSION_ID_calibration_audit.csv |
  Format-Table action,offset_hex,changes,unique_values,paired_exact_frame_events,paired_nearest_lag_median_frames -AutoSize
Import-Csv .\output\csv\horizontal_v1_4_SESSION_ID_termination.csv | Format-Table
```

Caution: these experiments **cannot yet determine angular units or scale** without independently measured signed aim displacement. Little-endian float32 is only a candidate interpretation, especially because addresses are not aligned. Reports never assert calibrated angles, and the existing operational export remains restricted to validated canonical symbols.
