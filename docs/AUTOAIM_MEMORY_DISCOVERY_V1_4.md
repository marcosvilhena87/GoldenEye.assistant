# v1.4 — Temporal Monitoring (experimental)

**No RDRAM writes, no auto-shot, no auto-align.** Five observed candidates are only hypotheses: `0x040A93`, `0x067D37`, `0x069AAD`, `0x0D308B`, `0x0D309B`. Three reproduced the strict ON/OFF controls in two v1.3 runs; two require investigation. Source of truth for validated symbols remains GoldenEye.mapping.

## Procedure

Stop prior collectors. From repository root run `git pull --ff-only origin main`, then `python tools/prepare_output.py` and `python -m unittest discover -s tests -v`. Confirm RDRAM name and size in BizHawk and manually set DOMAIN and EXPECTED_SIZE in `autoaim_memory_discovery_v1_4.lua`; launch that Lua script from the repository root. It samples five bytes every frame for at most 36,000 frames, recording new per-session timeline, transitions and operator marker CSVs under `output/csv`. It never touches v1.2/v1.2.1/v1.3 files.

Change game settings *manually*, then mark each observed event using e.g.:
```powershell
python .\tools\send_autoaim_mem_v1_4.py BASE_ON
python .\tools\send_autoaim_mem_v1_4.py BASE_OFF
python .\tools\send_autoaim_mem_v1_4.py ON_AGAIN
python .\tools\send_autoaim_mem_v1_4.py MENU_OPEN
python .\tools\send_autoaim_mem_v1_4.py MENU_CLOSED
python .\tools\send_autoaim_mem_v1_4.py OTHER_OPTION_CHANGED
python .\tools\send_autoaim_mem_v1_4.py NO_TARGET
python .\tools\send_autoaim_mem_v1_4.py TARGET_VISIBLE
python .\tools\send_autoaim_mem_v1_4.py WEAPON_CHANGE
python .\tools\send_autoaim_mem_v1_4.py LEVEL_RESTART
python .\tools\send_autoaim_mem_v1_4.py STOP
```
Commands only label the next observed frame; they do not alter the setting. The Lua collector accepts numbered commands and logs observed value transitions. Be sure to keep the game advancing; pause prevents command consumption.

Run `python tools/analyze_autoaim_mem_v1_4.py SESSION_ID` after completion. The result is a per-offset temporal summary, not proof of semantic identity. Markers can be correlated manually with transitions. Record ROM hash and BizHawk/N64 core alongside the session; none are attested automatically.

**Limitations:** A fixed per-frame sampler may miss transitions shorter than one frame. Invalid commands stop collection safely. Output files are created anew for each session; session collision fails instead of overwriting data. Do not publish ROM dumps.
