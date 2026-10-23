# Auto-Aim Memory Discovery v1.4.1 — Temporal Event Correlation

Offline analysis of existing v1.4 event and marker CSVs, **without new captures or memory access**.
The v1.4 session `20261023T204613Z_71121` is the intended first dataset. No input files are modified.

## Command
```powershell
git pull --ff-only origin main
python -m unittest discover -s tests -v
python .\tools\analyze_autoaim_mem_v1_4_1.py 20261023T204613Z_71121
```
Optional `--window 120 --episode-gap 3` (measured in frames). Output (new, never overwritten):
- `*_correlation_v1_4_1.csv`: nearest marker, signed event-minus-marker frame delta, proximity flag
- `*_episodes_v1_4_1.csv`: transitions grouped by inter-transition gap across offsets
- `*_pair_sync_v1_4_1.csv`: same-frame change counts for `0x0D308B` and `0x0D309B`
- `*_ramps_v1_4_1.csv`: monotonic increasing transition sequences with at least 3 steps

The marker is written **after** manual interaction in the existing protocol, so transitions before markers may be meaningful. A 120-frame window is a configurable heuristic, not evidence of causality or measured controller latency. Episodes and ramps are pattern descriptions, not object or field identifications.

No candidate is promoted to `validated` in GoldenEye.mapping. For stronger evidence, future protocols should bracket each action with before/after markers and capture ROM/core identification independently.
