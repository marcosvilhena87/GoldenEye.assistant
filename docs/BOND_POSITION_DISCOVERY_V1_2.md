# Bond Position Discovery v1.2 — Physical Axis Confirmation & Controlled Write Validation

## Evidence and safety
v1.1 showed large float32 BE variation at 0x0D33EC and 0x0D33F4, including changes under hold-labeled phases and constancy under FORWARD/BACK labels. Thus labels are operator intentions, **not evidence of actual motion**. A write to the Cheat Search word 0x0D33EC was reported by the operator; physical axis, scaling, format, persistence, ROM/core identity, and relation to camera remain unverified. v1.2 never writes game memory, never triggers inputs, and never promotes symbols.

## Setup
```powershell
cd C:\Minha_Pasta\Jogos\BizHawk-2.11.1-win-x64\Lua\N64\GoldenEye.assistant
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\output\csv,.\output\commands,.\output\sessions
```
Load `bond_position_discovery_v1_2.lua` from BizHawk Lua Console. It reads four aligned floats at 0D33E8/EC/F0/F4 through System Bus KSEG0 and KSEG1, flags changed raw bytes, emits an events CSV, and terminates on frame discontinuities such as savestate restores. It does **not** prove aliases agree with Cheat Search; check raw values manually.

## Physical movement protocol
Keep camera/heading fixed and Bond away from walls. Start and end each short action with an explicit marker, waiting for the console `MARKED` acknowledgement before starting or stopping physical movement. Never send all markers in a batch. Repeat from another position, and include stationary and pure-rotation controls.
```powershell
python .\tools\send_bond_position_v1_2.py BASELINE
python .\tools\send_bond_position_v1_2.py BEGIN_FORWARD
python .\tools\send_bond_position_v1_2.py END_FORWARD
python .\tools\send_bond_position_v1_2.py BEGIN_BACK
python .\tools\send_bond_position_v1_2.py END_BACK
python .\tools\send_bond_position_v1_2.py BEGIN_LEFT
python .\tools\send_bond_position_v1_2.py END_LEFT
python .\tools\send_bond_position_v1_2.py BEGIN_RIGHT
python .\tools\send_bond_position_v1_2.py END_RIGHT
python .\tools\send_bond_position_v1_2.py BEGIN_ROTATE
python .\tools\send_bond_position_v1_2.py END_ROTATE
```
After each END, hold stationary ~120 frames; record physical direction, relative camera behavior, any collision, and observed displacement outside the CSV.

## Optional independent manual-write protocol
Save a clean state **before starting a new capture**. Mark WRITE_PRE and record exact Cheat Search raw before-value. Perform a small, reversible manual write (never automated by these scripts), then mark WRITE_APPLIED once the emulator has advanced; capture held values for at least 120 frames and mark WRITE_OBSERVE. Document exact bytes, whether Bond moved visually, camera reaction, and estimated displacement. Do not restore savestate *inside* a capture; STOP first, restore, then start a separate session. Avoid blind writes or extreme values.

```powershell
python .\tools\send_bond_position_v1_2.py WRITE_PRE
python .\tools\send_bond_position_v1_2.py WRITE_APPLIED
python .\tools\send_bond_position_v1_2.py WRITE_OBSERVE
python .\tools\send_bond_position_v1_2.py STOP
$sid=(Get-Content .\output\sessions\bond_position_v1_2_session.txt -Raw).Trim()
python -m tools.analyze_bond_position_v1_2 $sid
```
Output files: `output/csv/bond_position_v1_2_<sid>_{timeline,markers,events,termination,discontinuities}.csv` and `_analysis.json`. All files are exclusive, to avoid overwriting evidence. The report computes marker-bounded displacement and 0/1/30/120 frame observational checkpoints, but **never marks axis or write persistence validated**. Cross-session replication, externally verified intervention timestamps, and camera-vs-Bond discrimination remain prerequisites.
