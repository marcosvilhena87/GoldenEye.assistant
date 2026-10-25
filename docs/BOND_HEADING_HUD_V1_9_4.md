# Bond Heading v1.9.4 — Live Calibration HUD

Read-only experimental monitor for the normalized candidate direction vector in GoldenEye 007 (N64) on BizHawk.

- RDRAM float32 big-endian X: `0x0D33F8`
- RDRAM float32 big-endian Y: `0x0D3400`
- `theta = degrees(atan2(y,x))`, with reference-relative heading and a cumulative unwrapped estimate.
- Valid vector when `abs(x*x+y*y-1)<0.02`.
- On-screen: X/Y, squared norm, mathematical heading, initial reference, relative heading, target, shortest signed angular error, accumulated angle and cumulative target remaining.
- A target of 360° has modulo target 0° but cumulative target 360°. Use the cumulative remaining display for a full revolution.
- A jump of 90° or greater between frames resets the integrated reference, prints a warning and prevents treating undersampled movement as continuous.

## Install / smoke test

```powershell
cd "C:\Minha_Pasta\Jogos\BizHawk-2.11.1-win-x64\Lua\N64\GoldenEye.assistant"
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_4 -v
```

Start `bond_heading_hud_v1_9_4.lua` in the BizHawk Lua Console with the **repository root as working directory**. Verify 8 MiB RDRAM and HUD rendering. The script does not write to the game or issue controls.

## Commands

Send **only one command at a time** and confirm `ACK` in the Lua Console:

```powershell
python -m tools.send_bond_heading_hud_v1_9_4 REFERENCE
python -m tools.send_bond_heading_hud_v1_9_4 TARGET_90
python -m tools.send_bond_heading_hud_v1_9_4 TARGET_180
python -m tools.send_bond_heading_hud_v1_9_4 TARGET_270
python -m tools.send_bond_heading_hud_v1_9_4 TARGET_360
python -m tools.send_bond_heading_hud_v1_9_4 TARGET_0
python -m tools.send_bond_heading_hud_v1_9_4 STOP
```

`REFERENCE` makes the **next valid measured orientation** the zero of the local relative-angle system. `TARGET_N` selects a positive mathematical-relative target, not an independently validated physical left turn. For left rotation the previous v1.9.3 run indicated negative increments, so use the signed error for a relative reference and watch cumulative angle for one or more loops.

## Experiment

1. Bond stationary. Send `REFERENCE`, wait for `ACK`, inspect relative ≈0.
2. Select a 90° target. Rotate gently, record relative angle and cumulative value at a visible landmark.
3. Repeat for 180°, 270°, and 360°. For exact return use shortest signed modulo error; for number of turns use cumulative value.
4. Reverse direction and compare heading at the same **visually identified landmark**.
5. Walk without turning, then change gun or aim independently. Confirm which actions change the candidate heading.
6. Repeat in fresh session and record N64 core, ROM identity/hash and memory domain. Distinguish camera orientation from Bond physical facing.

## Limits and validation
Angles displayed on the HUD are mathematically reconstructed from a vector: physical Bond-heading sign, zero axis and transform to world coordinates are not independently established. Do not freeze/write memory, perform auto-turn, or promote the offsets as validated heading in GoldenEye.mapping based only on the HUD. This is an observational tool and does not persist an experiment log; capture with the v1.9.2 Lua collector when framewise audit is needed.
