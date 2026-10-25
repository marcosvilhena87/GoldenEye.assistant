# Bond World Landmark Discovery v1.8.1 — Soldier Relative Coordinate Discovery

## Objective
Use a specific immobile enemy as a **relative reference** while changing EC (+128) or F4 (-128) in isolated Bond capture sessions. The known GameShark/cheat **Freeze All Enemies Alive** is a useful immobilization control, but a freeze of AI is not proof that the enemy's in-world position and coordinates are constant.

## Previous discovery sources
- `docs/FREEZE_ADDRESS_MAPPING_V1_1.md`: RAM Watch displayed physical 0x02C90C OFF=0, ON=255, and KSEG0/KSEG1 state transitions agreed in a previous trial; identity as a freeze status is provisional and not an enemy position or verified universal layout.
- `docs/ENEMY_COORDINATE_FULL_RAM_V1_8.md`: three freeze ON epochs P1/P2/P3 with a controlled camera snapshot; full 8 MiB read-only dump search for candidate float32 triples. No enemy XYZ yet validated.
- `docs/BOND_WORLD_LANDMARK_DISCOVERY_V1_8.md`: fixed-world geometry requirement.
- `tools/analyze_bond_coordinate_v1_6.py`: isolated Bond EC/F4 intervention and post-write checks.

## Experimental protocol
1. Load reproducible savestate where Bond and a **single visually identifiable guard** are in a safe, open area. Record guard identity, level, heading, camera viewpoint and ROM/core.
2. **OFF control:** with Bond immobile, leave freeze OFF to observe that the selected guard can move; save an isolated reference run. Do not confuse idle behavior with freeze effect.
3. Turn **Freeze All Enemies Alive ON manually**, after stopping the old capture, and confirm game behavior plus RAM Watch state and (if available) KSEG0/KSEG1 aliases of candidate 0x02C90C. Confirm steady ON before and after each Bond intervention. Do not change cheat mid-write or assume ON merely from a cheat checkbox.
4. Keep guard visibly tracked and stationary; inspect candidate enemy coordinates identified by the existing Enemy Coordinate Discovery v1.8. Search only, no new hardcoded XYZ addresses. Enemy identity/coordinate records must be validated independently of Bond EC/F4, including no ghost copies and no camera-only graphics buffer.
5. Record soldier candidate position before/after for >=120 frames, plus camera-only rotation control and no-write Bond control. A frozen guard with moving position records fails stationarity even if animation stops. No enemy coordinate candidate has yet been promoted canonical.
6. Restore clean original savestate, freeze ON, perform single Bond EC +128 or F4 -128 using v1.3 observer (wait MARKED on every command, and DONE stop). Check v1.6 isolated audit.
7. Record soldier position before and after and, **only if independently available**, Bond position in the same 2D coordinate frame (for example independent overhead survey). Position of Bond derived from candidate EC/F4 is **not** independent.
8. Use offline analyzer to test whether soldier drift is <= operator-set threshold and if the measured relative change is the negative of independently measured Bond displacement. Repeat heading 0/90/180 and optionally 270 to calibrate directions.

### Math and interpretation
Given soldier S and Bond B in the **same fixed reference**: `R = S - B`; `ΔR = ΔS - ΔB`. For a stationary soldier, `ΔS≈0` so `ΔR≈-ΔB`. The analyzer records `inverse_agreement_error = ||ΔR+ΔB||`; it equals the measured drift magnitude by construction and is only meaningful if observations are independent. Soldier memory coordinates alone do not provide Bond coordinates or make an FPS image an overhead map.

### Usage (after v1.6 audit for the Bond session exists)
```powershell
git pull --ff-only origin main
Copy-Item .\docs\BOND_SOLDIER_RELATIVE_V1_8_1_TEMPLATE.json .\output\bond_soldier_relative_v1_8_1.json
notepad .\output\bond_soldier_relative_v1_8_1.json
python -m tools.analyze_bond_soldier_relative_v1_8_1 .\output\bond_soldier_relative_v1_8_1.json
Get-Content .\output\bond_soldier_relative_v1_8_1_report.json
```
The template has **dummy coordinates**, false verification flags and an already-known Bond audit SID solely as an example. It is safe to execute but expected `eligible_runs: 0`. Replace it with operator-confirmed independent measurements and a suitable fresh SID. Analyses never overwrite reports. For new captures see `docs/BOND_COORDINATE_SYSTEM_VALIDATION_V1_6.md` and `docs/ENEMY_COORDINATE_FULL_RAM_V1_8.md`.

## Evidence levels
- Freeze state ON: practical experimental control, not coordinate proof.
- Soldier stopped on screen: useful observation, not independent 3D position proof.
- Validated enemy coordinate field stable across Bond movements and camera control: soldier landmark candidate.
- Bond independently located relative to verified enemy in the same frame: measured relative displacement candidate.
- Multiple independently calibrated angles/sessions with controls: evidence relevant to global-versus-relative axes.
- No canonical X/Z symbols promoted by this step.

## Safety
All new code is Python **offline read-only**. No cheat enabling, memory writes or GameShark codes are added. Freeze is an existing user-operated game cheat; preserve records of ON/OFF and ensure no unintended game state transitions.
