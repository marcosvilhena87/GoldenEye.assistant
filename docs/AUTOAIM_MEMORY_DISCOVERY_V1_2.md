# Auto-Aim Memory Discovery v1.2 — Candidate Validation (experimental)

This iteration watches **only the observed intersection of v1 and v1.1**, not all 8 MiB. Read-only, no auto-aim activation or writing to RAM.

## Requirements
- GoldenEye ROM and N64 core must be checked manually; record hash/core before interpreting results across sessions.
- The v1.1 CSV must have been produced with `--previous-v1-csv`: `in_v1_candidates=yes` identifies the 131 candidates in the current operator dataset.
- Stop previous Lua observer(s); work in the repository root; run `python .\tools\prepare_output.py`.
- Never copy unknown offsets into `GoldenEye.mapping/catalog/symbols.json`.

## Generate watchlist
```powershell
python .\tools\prepare_autoaim_mem_v1_2.py
```
Outputs:
- `output/commands/autoaim_mem_v1_2_watchlist.csv` with expected ON/OFF bytes and offsets
- `output/commands/autoaim_mem_v1_2_watchlist.json` describing input file SHA-256, watchlist SHA-256 and provenance.

Default input: `output/csv/autoaim_mem_v1_1_candidates_20261023T045912Z_104773.csv`. No candidate addresses are hardcoded in Lua or committed to GitHub. The number 131 is **expected for the user's latest CSV, not forced** by the script.

## Start observer
Edit **only after reconfirming domain and size in BizHawk**:
```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```
Open `autoaim_memory_discovery_v1_2.lua` in BizHawk Lua Console from the repository root. The collector creates a new session file and reads each observed offset with `memory.read_u8`. Unlike v1 and v1.1, each snapshot reads about 131 bytes rather than 8 MiB.

## Captures: operator manually changes game settings

| Stage | Auto-aim setting | Operator action |
|---|---|---|
| ON1 | ON | Baseline |
| ON_STABLE | ON | Remain in equivalent scene; no setting change |
| OFF1 | OFF | Toggle setting OFF |
| OFF_STABLE | OFF | Keep OFF |
| ON2 | ON | Toggle ON |
| MENU_NO_CHANGE | ON | Open/close menu without changing auto-aim |
| OFF2 | OFF | Toggle OFF again |
| ON3 | ON | Toggle ON again |

**One command at a time**, after setting the indicated state and checking the previous `captured ...` message:
```powershell
python .\tools\send_autoaim_mem_v1_2.py ON1
python .\tools\send_autoaim_mem_v1_2.py ON_STABLE
python .\tools\send_autoaim_mem_v1_2.py OFF1
python .\tools\send_autoaim_mem_v1_2.py OFF_STABLE
python .\tools\send_autoaim_mem_v1_2.py ON2
python .\tools\send_autoaim_mem_v1_2.py MENU_NO_CHANGE
python .\tools\send_autoaim_mem_v1_2.py OFF2
python .\tools\send_autoaim_mem_v1_2.py ON3
```

Before changing state, make sure the prior label is present in `output/csv/autoaim_mem_v1_2_manifest.csv`. The sender creates a unique numbered command and does not overwrite previous requests. **The command itself never changes a game setting.**

## Analysis
```powershell
python .\tools\analyze_autoaim_mem_v1_2.py
```

Strictly consistent candidates satisfy:
- ON1 = ON_STABLE = ON2 = MENU_NO_CHANGE = ON3
- OFF1 = OFF_STABLE = OFF2
- ON value differs from OFF value.

The report `output/csv/autoaim_mem_v1_2_validation_<session>.csv` distinguishes `candidate_repeated_controls_only` from `failed_candidate_controls`. It makes **no causal or validated-symbol claim**.

**Known limitations:** Only one byte per offset; expected ON/OFF values in watchlist are provenance, not directly used to decide current-session consistency. No independent ROM identification or emulator-core attestation. No control with an entirely different menu option or no-target context yet. Restart/reload repetition is still required before considering promotion in `GoldenEye.mapping`.
