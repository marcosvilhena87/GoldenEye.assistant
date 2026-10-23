# Auto-Aim Horizontal Correction Discovery v1 — Exploratory spatial contrasts

Goal: find candidate *memory bytes* varying with left/center/right aim assistance, not the already identified ON/OFF switch. This phase does NOT identify horizontal correction, an angle, Bond heading, a target pointer, or memory structure. ROM identity, core, and scene geometry still need independent verification.

## Operator protocol

From `GoldenEye.assistant`, run `python tools/prepare_output.py` and the unit tests. Verify RDRAM size 8388608, then explicitly configure `DOMAIN` and `EXPECTED_SIZE` in `horizontal_correction_discovery_v1.lua` and start it in BizHawk. Keep Bond still, same weapon, same distance and static single target, steady camera where feasible. Identify ROM SHA-256 and BizHawk N64 core separately before claiming reproducibility.

Use one request at a time. Arrange the scene and wait for a stable state **before** sending each:
1. `ON_NO_TARGET`: Auto-Aim ON, no eligible enemy.
2. `ON_LEFT`: ON, target to left.
3. `ON_CENTER`: ON, target centered.
4. `ON_RIGHT`: ON, target to right.
5. `OFF_LEFT`: Auto-Aim OFF, target left.
6. `OFF_CENTER`: OFF, centered.
7. `OFF_RIGHT`: OFF, right.
8. `ON_LEFT_REPEAT`: ON, recreate the left scene.

Request syntax:
```powershell
python .\tools\send_horizontal_v1.py ON_NO_TARGET
```
Then use the next label. Verify Lua `captured LABEL` and per-session manifest entry before proceeding. Eight 8-MiB dumps total ~64 MiB, local only, not for upload to the repository. Each snapshot takes time and is not time-atomic; ideally pause scene or ensure stability. If label scene cannot be recreated comparably, discard interpretation, do not invent significance.

After eight captures:
```powershell
python .\tools\analyze_horizontal_v1.py SESSION_ID
```
A candidate is a **byte** that (i) differs in all three ON spatial conditions; (ii) stays identical across all three OFF conditions; (iii) returns to the first ON_LEFT value upon replay. This screen may miss real multi-byte float/angular fields or dynamic in-game correction. It does NOT prove spatial monotonicity, direction, units, or semantics. Negative controls, temporal stability, independent run and width/endianness investigation are required next. Do not write to RAM or enable auto-align.
