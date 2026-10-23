# Auto-Aim Memory Discovery v1.2.1 — Atomic Requests

The previous v1.2 session `20261023T194744Z_9735` contains four confirmed captures (ON1, ON_STABLE, OFF1, OFF_STABLE), 131 bytes each. Preserve `output/csv/autoaim_mem_v1_2_manifest.csv` and `autoaim_mem_v1_2_samples.csv` exactly as they are. No automated migration or modification of historical evidence is performed.

## Preparation

1. Stop the v1.2 Lua collector.
2. Confirm RDRAM size (8 MiB) using BizHawk and set `DOMAIN`/`EXPECTED_SIZE` explicitly in `autoaim_memory_discovery_v1_2_1.lua`.
3. From the repository root, run `python tools/prepare_output.py` and `python tools/prepare_autoaim_mem_v1_2.py` (existing 131-candidate watchlist).
4. Run `python -m unittest discover -s tests -v`.
5. Open `autoaim_memory_discovery_v1_2_1.lua` in BizHawk Lua Console.

The collector creates isolated `output/csv/autoaim_mem_v1_2_1_manifest_<session>.csv` and `autoaim_mem_v1_2_1_samples_<session>.csv`. It does not edit the v1.2 files. Start one collector only, and archive session evidence before running it again.

## Eight manual captures

Set the in-game option yourself (commands do not toggle Auto-Aim). Submit one request at a time, verifying the Lua `captured` message and session-specific CSV before submitting another:

```powershell
python .\tools\send_autoaim_mem_v1_2_1.py ON1
python .\tools\send_autoaim_mem_v1_2_1.py ON_STABLE
python .\tools\send_autoaim_mem_v1_2_1.py OFF1
python .\tools\send_autoaim_mem_v1_2_1.py OFF_STABLE
python .\tools\send_autoaim_mem_v1_2_1.py ON2
python .\tools\send_autoaim_mem_v1_2_1.py MENU_NO_CHANGE
python .\tools\send_autoaim_mem_v1_2_1.py OFF2
python .\tools\send_autoaim_mem_v1_2_1.py ON3
```

Atomic publication: Python writes/fsyncs a `.pending` file on the same volume, then renames it to the final filename. Lua accepts only exact session/label content and never captures invalid commands. If a command is invalid, stop, inspect, and correct it *without changing prior evidence*.

After completing eight captures, use the v1.2 analyzer only on a separately prepared copy or with explicitly configured v1.2.1 file inputs; never replace original v1.2 data. No address is validated or promoted by this procedure.

Note: The collector creates session-specific CSV files but uses a single current-session pointer `output/sessions/autoaim_mem_v1_2_1_session.txt`; do not run multiple collectors or restart with the same session ID.
