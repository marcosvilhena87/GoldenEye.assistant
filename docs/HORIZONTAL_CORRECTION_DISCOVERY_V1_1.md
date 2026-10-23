# Horizontal Correction Discovery v1.1 — Typed Offline Interpretation

## Scope

This tool reuses the existing v1 session's eight local RDRAM dumps and the original candidate CSV. No new game capture required. It does not read or write emulator memory, does not amend the original v1 output and does not promote experimental symbols.

- Reinterprets candidate neighborhoods as signed `int16`, signed `int32` and IEEE-754 `float32`, each in big- and little-endian.
- A starting offset may be up to three bytes before a v1 byte candidate; fields are **not assumed aligned**.
- Rejects non-finite floating-point interpretations.
- Retains typed interpretations where ON-left, ON-center and ON-right are distinct, all three OFF values are equal, and ON-left replay matches.
- Reports whether ON-left actually differs from OFF-left, and whether the ON values are strictly monotonic. These are descriptive labels, **not conclusive ranking or proof**.
- A typed candidate can overlap other candidates; these are alternative interpretations of the same bytes.

## Execution (PowerShell)

```powershell
git pull --ff-only origin main
python -m unittest discover -s tests -v
python .\tools\analyze_horizontal_v1_1.py 20261023T220715Z_346211
Import-Csv .\output\csv\horizontal_v1_1_typed_candidates_20261023T220715Z_346211.csv |
  Where-Object { $_.on_off_left_differs -eq 'True' -and $_.monotonic_on -eq 'True' } |
  Select-Object -First 30 | Format-Table -AutoSize
```

Requires all eight `output/archive/horizontal_v1_<SESSION>_<LABEL>.bin` files (~64 MiB), the v1 manifest and candidate CSV. The output filename is new and immutable; rerunning refuses overwrite. Missing input or incompatible sizes cause an error.

## Caveats

Single snapshots are not temporally atomic; scene position, enemy state and Bond/camera heading were not proven identical across captures. A memory value constant under OFF and variable under ON may be a side effect. Float32 values close to zero or integer wrap require further analysis; signed fixed-point and other formats may be missed. ROM/core identity and horizontal correction remain unvalidated. Do not enable Auto-Align or Auto-Shot.
