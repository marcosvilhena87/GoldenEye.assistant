# Auto-Aim Memory Discovery v1.3 — Independent Validation

## Provenance
Five observed candidates from the completed v1.2.1 run `20261023T200459Z_70077`, all **unvalidated**:
- `0x040A93` (previous ON=1, OFF=0)
- `0x067D37` (previous ON=63, OFF=15)
- `0x069AAD` (previous ON=58, OFF=56)
- `0x0D308B` (previous ON=1, OFF=0)
- `0x0D309B` (previous ON=1, OFF=0)

No historic evidence file is modified. v1.3 writes its own per-session CSVs. The code reads RDRAM only; it does not toggle Auto-Aim, inject controller inputs, or write memory.

## Two truly independent runs
1. From the repo root, run `python tools/prepare_output.py`. Stop all older Lua observers. Confirm BizHawk **RDRAM = 8388608 bytes** and set `DOMAIN="RDRAM"` and `EXPECTED_SIZE=8388608` in `autoaim_memory_discovery_v1_3.lua`.
2. Record ROM hash, BizHawk version, N64 core, save state/level and date externally. They are **not** auto-attested by this collector.
3. Load the v1.3 Lua observer, record its session ID. New CSVs use `output/csv/autoaim_mem_v1_3_{manifest,samples}_<session>.csv`.
4. Manually set each state, then issue one corresponding command and verify the Lua capture and CSV manifest **before proceeding**:
```powershell
python .\tools\send_autoaim_mem_v1_3.py ON_BASE
python .\tools\send_autoaim_mem_v1_3.py ON_STABLE
python .\tools\send_autoaim_mem_v1_3.py OFF1
python .\tools\send_autoaim_mem_v1_3.py OFF_STABLE
python .\tools\send_autoaim_mem_v1_3.py ON2
python .\tools\send_autoaim_mem_v1_3.py MENU_CONTROL
python .\tools\send_autoaim_mem_v1_3.py OTHER_OPTION_CONTROL
python .\tools\send_autoaim_mem_v1_3.py NO_TARGET_ON
```
Interpretation:
- `ON_BASE`, `ON_STABLE`: Auto-Aim ON, comparable gameplay scene and no option changes
- `OFF1`, `OFF_STABLE`: Auto-Aim OFF, comparable scene
- `ON2`: ON again, comparable scene
- `MENU_CONTROL`: open/close menu **without changing** Auto-Aim; still ON
- `OTHER_OPTION_CONTROL`: change *another unrelated option*, keep Auto-Aim ON and document which option
- `NO_TARGET_ON`: Auto-Aim ON, gameplay scene with no valid target in range; document context

5. After completion, **fully restart the emulator and game** and repeat the same eight steps under a fresh session. Do not merely reload the Lua script. Verify the game is the same ROM/core.
6. Analyze after both completed runs:
```powershell
python .\tools\analyze_autoaim_mem_v1_3.py SESSION_A SESSION_B
```
The analyst refuses incomplete/duplicate captures and generates a new report without overwriting existing reports. A `reproduced_candidate_controls_only` result requires consistent ON and OFF bytes in each session and the **same** ON/OFF pair across sessions. This is stronger observational evidence, **not a demonstrated causal mapping** or a horizontal aiming correction signal.

## Safety and limitations
- No memory symbols are promoted into `GoldenEye.mapping`; do not infer semantic meaning from correlations.
- Both runs require manual confirmation of game option state, ROM identity, and N64 core. The recorder cannot independently verify those assertions.
- Opening/restarting one script may overwrite only the **active v1.3 session pointer**, never historical per-session CSVs. Archive manifests and samples after each run.
- Do not start two collectors concurrently.
