# Bond Position Discovery v1.1 — Float32 Coordinate & Axis Validation

## Scope and evidence
Operator reports Cheat Search write at 0x0D33EC moved Bond; v1.0.4 recorded KSEG0=KSEG1 469D at capture start. Reading KSEG aliases does not prove physical axis or true float representation. v1.1 is **read-only**, observes aligned 32-bit candidates at 0D33E8, 0D33EC, 0D33F0, 0D33F4 via System Bus KSEG0 and KSEG1, and decodes IEEE754 BE explicitly. No Lua writes, input injection, or automatic axis promotion.

## Setup
From repository root, create `output/csv`, `output/commands`, `output/sessions`. Load `bond_position_discovery_v1_1.lua` in BizHawk. Each command labels the **subsequent** interval, not the prior action. Run separately (wait for MARKED after each):
```powershell
python .\tools\send_bond_position_v1_1.py BASELINE
python .\tools\send_bond_position_v1_1.py FORWARD
python .\tools\send_bond_position_v1_1.py HOLD_F
python .\tools\send_bond_position_v1_1.py BACK
python .\tools\send_bond_position_v1_1.py HOLD_B
python .\tools\send_bond_position_v1_1.py STRAFE_LEFT
python .\tools\send_bond_position_v1_1.py STRAFE_RIGHT
python .\tools\send_bond_position_v1_1.py ROTATE
python .\tools\send_bond_position_v1_1.py HOLD_ROT
```
Keep each hold >=120 frames, record physical direction, heading, walls and any camera motion externally. For optional manual Cheat Search write: make independent savestate, mark WRITE_BEFORE; at restored baseline change **only one verified field** by a small, reversible value; mark WRITE_AFTER then WRITE_HOLD1, WRITE_HOLD30, WRITE_HOLD120 at relevant actual times; capture 1/30/120 frames via annotations; mark RESTORE after restoring. Markers do NOT automate timing; no assumption they occurred on exact frames. Avoid random or extreme values. A savestate reload creates a timeline discontinuity and stops this collector; use a new session file after restore. Send STOP after all phases and before loading any savestate when possible:
```powershell
python .\tools\send_bond_position_v1_1.py STOP
```
Sender writes one immutable session-tagged command; wait for MARKED before sending next. Captures: `output/csv/bond_position_v1_1_<sid>_timeline.csv`, `_markers.csv`, `_termination.csv`, `_discontinuities.csv`. Termination reason stop confirms clean collection. Float values can be absent for NaN/Inf and will be flagged. Compare to Cheat Search and reproduce in a fresh session before identifying axes; camera/geometry evidence is external.

## Validation gate
A coordinate claim requires repeated independent real-world movement, stationary and pure-rotation negative controls, return behavior, held-write persistence, cross-session stability and ROM/core identification. Do not promote mapping symbol or feed movement automation based on this v1.1 alone.
