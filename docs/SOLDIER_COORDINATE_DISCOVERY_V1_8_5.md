# Soldier #1 Coordinate Discovery v1.8.5 — Bond-Referenced RDRAM Search

Experimental only. Stage snapshots are manually verified; **no X/Z and no Soldier identity is automatically validated**. Mission/Part context: operator reports Mission 1 Arkangelsk, Part I Dam for historical experiments; record actual context for each new save.

## Capture
Prerequisites: BizHawk 2.11.1, the observed `RDRAM` domain of exactly 8,388,608 bytes, output/archive, output/csv, output/sessions, output/commands. Stop other collectors; do not load a savestate *during* a snapshot; allow Lua to print CAPTURED before the next action. Run `soldier_coordinate_discovery_v1_8_5.lua` from repository root in Lua Console. It only reads memory. Every stage writes a distinct 8MiB binary (at least 40MiB total) to output/archive, locally only; never commit dumps or copyrighted saves.

Send `python -m tools.send_soldier_coordinate_v1_8_5 LABEL` one at a time:
1. BASELINE: Bond and a uniquely identified Soldier #1 stationary (preferably Freeze enabled).
2. BOND_ROTATE: Bond rotates without translating, same soldier frozen; separate from BASELINE.
3. BOND_MOVE: Bond translates with camera held as constant as possible, soldier frozen.
4. SOLDIER_MOVE: Bond stationary again; same soldier visibly moving with Freeze disabled. **The sequence is not identical geometry** because Bond moved; record reference return to original position separately.
5. SOLDIER_FREEZE: soldier manually frozen at new location, Bond stationary. Snapshot cannot prove continuous stability.
6. Optionally NEW_SAVE: new save (same Mission/Part preferred), with fresh context. This snapshot is for provenance; cross-save validation requires a complete independently controlled new session.
7. STOP: close manifest; expect DONE stop.

Each command is published atomically. Confirm CAPTURED and wait for Lua before sending another. The collector detects savestate discontinuity only between polling frames; switching saves must be done between finished captures and documented. A genuine savestate reset that changes emulated framecount may stop collection. For cross-save scans, use separate runs and compare reports.

## Analysis
`$sid=(Get-Content .\output\sessions\soldier_coordinate_v1_8_5_session.txt -Raw).Trim()`
`python -m tools.analyze_soldier_coordinate_v1_8_5 $sid`

It scans aligned 32-bit floats in BE and LE and ranks RAW changes during SOLDIER_MOVE, no changes during BOND_ROTATE, and optional proximity to **unverified** Bond candidate anchor values. No global claim is made based on proximity. The frozen snapshot is only a single endpoint. There is no automatic coordinate validation, pointer chain resolution or integer scan in this initial version.

Results must be cross-checked against independently observed Soldier #1 motion and repeat saves. Keep old offsets 0x20F594/0x20F5AC as historical experiments, not persistent mappings. Source-of-truth candidates: GoldenEye.mapping. ROM SHA-256 and core ID are pending confirmation.
