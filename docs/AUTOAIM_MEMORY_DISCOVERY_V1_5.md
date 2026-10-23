# Auto-Aim Memory Discovery v1.5 — Semantic Field Identification

v1.5 tracks five *experimental* RDRAM bytes every frame, using operator **BEGIN/END** markers to bracket a single manual change. No memory writes, auto-aim controller, auto-align or auto-shot. Original v1.2–v1.4.1 data is never modified.

## Preparation
- Stop all other collectors. Update using `git pull --ff-only origin main`.
- Run `python tools/prepare_output.py` and `python -m unittest discover -s tests -v`.
- Confirm ROM hash and emulator N64 core manually. Confirm `RDRAM` domain has `8388608` bytes.
- Set `DOMAIN="RDRAM"` and `EXPECTED_SIZE=8388608` **only after verifying** in `autoaim_memory_discovery_v1_5.lua`, then open it in BizHawk Lua Console at the repo root.
- Take each action in a controlled and comparable gameplay scene; change only one condition per window.

## Marking
1. Send `python .\tools\send_autoaim_mem_v1_5.py BEGIN_AUTOAIM_OFF`.
2. Confirm Lua printed `marked BEGIN_AUTOAIM_OFF` **before** touching the game menu.
3. Disable auto-aim manually, return to gameplay, confirm it is OFF.
4. Send `python .\tools\send_autoaim_mem_v1_5.py END_AUTOAIM_OFF` and confirm Lua.
5. Do the matching `BEGIN_AUTOAIM_ON` and `END_AUTOAIM_ON` pair after switching ON.
6. Repeat with `MENU_ONLY`, `OTHER_OPTION`, `NO_TARGET`, `TARGET_VISIBLE`, `WEAPON_CHANGE` or `LEVEL_RESTART` using `BEGIN_<ACTION>` and `END_<ACTION>`. Return to stable gameplay between windows.
7. Finish with `python .\tools\send_autoaim_mem_v1_5.py STOP` when no action is open. The collector also stops automatically after 36000 frames.

The sender validates bracket order and publishes commands atomically. It **does not** change game state. The observer records timestamped data under `output/csv/autoaim_mem_v1_5_<session>_*.csv`, and current session ID under `output/sessions/autoaim_mem_v1_5_session.txt`.

Analyze completed windows:
```powershell
python .\tools\analyze_autoaim_mem_v1_5.py ID_DA_SESSAO
```
Output `*_semantic_windows.csv` includes before, begin, end and after byte values, within-window changes, and distinct values. CSV is never overwritten. Action windows correlate observational data with operator assertions; they do **not** prove semantic identity. To test horizontal aiming correction, a separate validated measurement protocol is needed.

**Warning:** a STOP immediately after END has no post-window baseline. Allow a few frames between END and STOP. If collector stops mid-window, analyze only after a complete new controlled run. No new symbols are promoted into GoldenEye.mapping.
