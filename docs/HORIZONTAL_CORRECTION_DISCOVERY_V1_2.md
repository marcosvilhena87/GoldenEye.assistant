# Auto-Aim Horizontal Correction Discovery v1.2 — Temporal Candidate Validation

Experimental, read-only per-frame observation of **two v1.1 leads**: RDRAM `0x0D3995` and `0x0D3D3D`, four raw bytes each. These offsets are neither aligned/validated float symbols nor confirmed horizontal correction. The observer logs raw bytes; offline decoding as little-endian float32 is a *hypothesis*.

## Setup

1. Run `git pull --ff-only origin main` and `python -m unittest discover -s tests -v`.
2. Verify the BizHawk RDRAM domain and its 8,388,608 byte size. Set `DOMAIN="RDRAM"` and `EXPECTED_SIZE=8388608` explicitly at the top of `horizontal_correction_discovery_v1_2.lua`.
3. Run the Lua file in BizHawk. Record its `[horizontal.v1.2] session=...` line.
4. Use `python .\tools\send_horizontal_v1_2.py BEGIN_STATIONARY_CONTROL`; wait for **Lua marked** before observing an unchanged scene; then `END_STATIONARY_CONTROL`. Wait for marked END.
5. Keep Bond fixed and one enemy in a stable position. With Auto-Aim ON, bracket `TARGET_LEFT`, `TARGET_CENTER`, `TARGET_RIGHT`, one at a time; note operator scene preparation must occur **inside** each BEGIN/END interval for transition detection. For movement controls, also bracket `BOND_TURN_LEFT`, `BOND_TURN_RIGHT` with no eligible target; bracket `NO_TARGET` when appropriate.
6. For the critical A/B test, keep Bond, camera, weapon and enemy geometry unchanged; bracket `AUTOAIM_OFF` and then `AUTOAIM_ON` (change setting *after BEGIN*). After each END, check marker in CSV.
7. Use `STOP` while no action is active. Prefer a fresh session if nearing the collector's 36,000-frame cap.

## Offline analysis

```powershell
python .\tools\analyze_horizontal_v1_2.py SESSION_ID
Import-Csv .\output\csv\horizontal_v1_2_SESSION_ID_windows.csv | Format-Table action,offset_hex,changes,distinct_raw,first_f32_le,last_f32_le -AutoSize
```

Raw and event CSVs: `output/csv/horizontal_v1_2_<session>_{timeline,events,markers}.csv`; read-only output. Analyzer writes an immutable, independent `*_windows.csv` and refuses overwrite.

## Interpretation gates

- A variable that follows target movement even when auto aim OFF may represent *target state*, not correction.
- A field that varies with Bond rotation in NO_TARGET scenes may represent *camera/Bond heading* rather than correction.
- OFF/ON effects with fixed geometry and stable baselines improve association but do not identify semantics.
- Little-endian float values from unaligned addresses may be artifacts; compare adjacent aligned 4-byte words in future experiments.
- An independent repeat, ROM SHA-256/core identity, spatial calibration, and negative controls are required before mapping promotion.
- No memory writes, automatic rotation or firing are implemented.
