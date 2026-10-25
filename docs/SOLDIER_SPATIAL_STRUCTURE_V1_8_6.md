# Soldier Coordinate Discovery v1.8.6 — Spatial Structure Correlation

This experiment samples aligned 4-byte raw words at the v1.8.5 candidate families and ±8-byte neighborhoods, on each emulator frame. It is **read-only**, and addresses are experimental. Do not infer XYZ, the original source of duplicated fields, or that the same soldier structure persists across saves.

## Setup
From repository root, create `output/csv`, `output/commands`, `output/sessions`; stop other Lua collectors and load `soldier_spatial_structure_v1_8_6.lua` in BizHawk. The Lua script checks exactly 8 MiB of RDRAM and writes a session ID to `output/sessions/soldier_spatial_v1_8_6_session.txt`.

Send one marker at a time with `python -m tools.send_soldier_spatial_v1_8_6 LABEL`, waiting for `MARKED`, observing at least 120 frames per phase:
1. BASELINE — Bond and visually identified soldier stationary.
2. BOND_ROTATE — rotate view without translating Bond, soldier frozen.
3. BOND_MOVE — translate Bond, soldier frozen.
4. SOLDIER_MOVE — Bond stationary, same soldier moving.
5. SOLDIER_FREEZE — manually freeze the same soldier, verify stationary.
6. STOP — expect `DONE stop`.

For a new save, **start a new Lua session**, preserve both SIDs and repeat the controlled protocol. The `NEW_SAVE` marker is optional metadata only and does not establish identity. Never load savestates during active logging, which detects framecount discontinuities.

## Analysis
`$sid=(Get-Content .\output\sessions\soldier_spatial_v1_8_6_session.txt -Raw).Trim()`
`python -m tools.analyze_soldier_spatial_v1_8_6 $sid`

Output includes per-address transition counts by phase, pairs with co-change Jaccard >= 0.7, exact duplicate raw series fraction, and hypothetical constant differences under float32 big-endian. The report preserves capture integrity flags. Temporal correlation cannot determine source-vs-copy or XYZ. Keep raw CSV local and do not add symbols to mapping until spatial validation, save comparisons, and ROM/core checks.
