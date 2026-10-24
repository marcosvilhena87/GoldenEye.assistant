# Dual RDRAM U8 Probe v1: 0D36F4 / 0D3720

User reported Cheat Search rows `0D36F4 d u 1 RDRAM` and `0D3720 d u 1 RDRAM`. These are **8-bit unsigned candidate offsets**, not known Bond coordinates, headings or Auto-Aim fields. Code search found no prior exact references. Their proximity to earlier offsets does not imply shared semantics.

The corresponding **unverified and unobserved** candidates are registered in `GoldenEye.mapping/catalog/candidates.json` with audit record `experiments/dual_u8_0d36f4_0d3720_intake_20261024.json`. No canonical symbols added.

## Setup

From project root, run `python .\\tools\\prepare_output.py` if output directories are missing. In BizHawk, independently verify the exact memory-domain name and size using `memory.getmemorydomainlist()` and `memory.getmemorydomainsize("RDRAM")`. Only then edit `probe_0d36_0d37_v1.lua` to set:

```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```

Load the script in BizHawk; it only reads two bytes per frame, does not write memory or inject controls. Sender writes exactly one command per invocation to a session-scoped file. Wait for `marked LABEL` before changing state. Do not restart collector, load savestates, or change ROM during capture.

## Suggested controlled phases (each 120+ frames, after the marker)

```powershell
python .\\tools\\send_probe_0d36_0d37_v1.py BASELINE
python .\\tools\\send_probe_0d36_0d37_v1.py FORWARD
python .\\tools\\send_probe_0d36_0d37_v1.py STOP_MOVE
python .\\tools\\send_probe_0d36_0d37_v1.py ROTATE
python .\\tools\\send_probe_0d36_0d37_v1.py STOP_ROTATE
python .\\tools\\send_probe_0d36_0d37_v1.py BACK
python .\\tools\\send_probe_0d36_0d37_v1.py NO_TARGET
python .\\tools\\send_probe_0d36_0d37_v1.py TARGET_VISIBLE
python .\\tools\\send_probe_0d36_0d37_v1.py AUTOAIM_OFF
python .\\tools\\send_probe_0d36_0d37_v1.py AUTOAIM_ON
python .\\tools\\send_probe_0d36_0d37_v1.py WEAPON_CHANGE
python .\\tools\\send_probe_0d36_0d37_v1.py STOP
```

**Do not send all commands at once.** Each should delimit one operator-controlled interval; if a contrast cannot be performed, skip that label rather than manufacture an intervention. Capture with negative controls and repeat across an independent game session. Use `STOP` to finish.

Output: `output/csv/probe_0d36_0d37_<session>_{timeline,markers,termination,discontinuities}.csv`. Every frame captures both hex and unsigned decimal bytes and whether they changed. Check `reason=stop` and no discontinuities. A marker only records the operator label: it does **not** verify that the game action occurred.

For a quick local preview:

```powershell
$s=(Get-Content .\\output\\sessions\\probe_0d36_0d37_session.txt -Raw).Trim()
Import-Csv ".\\output\\csv\\probe_0d36_0d37_${s}_timeline.csv" |
 Group-Object phase,offset_hex |
 Select-Object Name,Count,@{n='Distinct';e={(@($_.Group.u8 | Sort-Object -Unique)).Count}} |
 Format-Table -AutoSize
```

Do not promote these bytes to a validated function before controlled positive/negative evidence, independent reproduction, ROM SHA/core verification, and addressing alias checks.
