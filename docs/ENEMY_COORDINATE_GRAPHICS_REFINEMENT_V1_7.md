# Enemy Coordinate Discovery v1.7 — Graphics Buffer Exclusion & Coordinate Search Refinement

## Motivation
Previous v1.6 analysis of session `20261024T230404Z_651462` produced 3,687 temporal interpretations and 365 screened interpretations. User-provided sample words in both A and B include `E7000000`, `F8000000`, `FB000000`, `FC159804`, `B900031D`, `BC000C06` and `BA001402`. Several are compatible with Nintendo 64 display-list opcodes. That is a hypothesis **not** formal microcode/disassembly validation.

## Method (read-only)
- Reuse the v1.6 manifest and its three ON STABLE/HOLD periods plus any CAM snapshot. Enforce same-frame metadata and exact capture lengths through `validate_manifest`.
- Scan each captured region in aligned eight-byte words. Every 64-byte window must include at least three first-byte opcodes from an exploratory RSP/RDP-compatible set, at least two distinct opcodes, and at least one strong command candidate (`E7`, `F8`, `FB`, `FC`). **One opcode alone never excludes a window.**
- Union flagged windows across the three positions and mark intersecting bytes as graphics-context suspicion, **not** demonstrated display lists or permanent exclusion.
- Re-evaluate each 4-byte-aligned word in the three captured regions. Require full-word ON HOLD stability across P1/P2/P3 and changes P1→P2 and P2→P3.
- Interpret 4-byte values as both big- and little-endian float32. Require all three finite, within ±1,000,000; and both numerical deltas between 0.0001 and 100,000 magnitude. Thresholds are heuristic, not scale/coordinate validation.
- Flag camera sensitivity (if a CAM snapshot was actually captured) and suspected graphics overlap. Only those with neither flag get `numeric_candidate_only`.

## Run
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_7 -v
$sid="20261024T230404Z_651462"
python -m tools.analyze_enemy_freeze_v1_7 $sid
Import-Csv ".\output\csv\enemy_freeze_v1_7_${sid}_numeric_candidates.csv" | Where-Object status -eq "numeric_candidate_only" | Select-Object -First 30 | Format-Table -AutoSize
```

## Outputs
- `output/csv/enemy_freeze_v1_7_<sid>_graphics_windows.csv`
- `output/csv/enemy_freeze_v1_7_<sid>_numeric_candidates.csv`
- `output/csv/enemy_freeze_v1_7_<sid>_summary.json`

These new reports never overwrite existing ones; source captures are untouched.

## Critical limitations
This is **refinement within three sampled regions**, **not a scan of the complete 8 MiB RAM**. Graphics opcodes depend on the microcode and opcode-byte context; no firm buffer mapping is established. Numerical float32 interpretations are exploratory; spatial units, directions, object association and XYZ not known. The CAM marker documents capture but not camera-only physical ground truth. Sign/delta in RAM cannot be compared to unmeasured physical motion. `GoldenEye.mapping` retains hypotheses and does not promote confirmed XYZ.
