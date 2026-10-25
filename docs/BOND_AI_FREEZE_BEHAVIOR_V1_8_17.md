# GoldenEye v1.8.17 — Freeze Integrity & Behavioral Correlation

**Offline audit** of the existing v1.8.16 timeline, with optional manually annotated visual events. No memory writes and no BizHawk restart required for initial analysis.

## Motivation
The v1.8.16 first decoupling showed A changing 201 times during `DECOUPLE_MOVE` while the A/B gap reached 1408; the repeat showed 219 A changes and a gap of ~1424.8. Individual phase transitions do not identify when the Freeze toggle actually took effect, nor whether the active Freeze was continuous. Test equality of **RAW pairs across phases**, and distinguish an inferred numerical release from the soldier's observed actions.

A = `0x06D248/0x06D250` (candidate AI target); B = `0x0D33EC/0x0D33F4` (candidate Bond position).

## Analyze the existing v1.8.16 capture
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_ai_freeze_v1_8_17 -v
$sid="20261025T184928Z_10702"
python -m tools.audit_bond_ai_freeze_v1_8_17 $sid
$r=Get-Content ".\output\csv\bond_ai_v1_8_17_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.treatments | Format-List
$r.phase_integrity | Format-List
$r.first_release_a_only_change | Format-List
```
By phase, the report counts unique RAW vectors, changes within that phase, and the first/last/maximum A–B numeric gap. The cross-phase `first_freeze` and `repeat_freeze` checks are stricter than a phase-local stability check. The first release event is the earliest recorded change in A with B constant during release/observation phases.

## Optional visual observation correlation
If video/frame counts or contemporaneous notes exist, create an operator-supplied CSV:
```csv
session,frame,event,confidence,notes
20261025T184928Z_10702,12345,SOLDIER_OLD_TARGET_VISUAL,medium,Still pursuing older location
20261025T184928Z_10702,12400,SOLDIER_RETARGET_VISUAL,high,Turned toward current Bond
```
Use **actual frame numbers from the same capture**. These are examples, not observed frames; do not copy them blindly. Events accepted: `SOLDIER_OLD_TARGET_VISUAL`, `SOLDIER_RETARGET_VISUAL`, `NO_RETARGET_VISUAL`, `UNCERTAIN`. The program calculates frame difference to the first numerical release event and reports uncertainty; it does not classify AI direction from RAM values.

```powershell
python -m tools.audit_bond_ai_freeze_v1_8_17 $sid --observations .\output\csv\operator_observations.csv
```
**Important:** the report refuses to overwrite an existing analysis JSON. Use a fresh output directory with `--root` containing the input CSV, or rename/backup the old v1.8.17 report first if adding observations.

## Next controlled repeat
For stronger evidence, record the actual frame where Freeze toggles ON/OFF in BizHawk, measure whether A remains constant across the whole active interval, and record the frame when the soldier demonstrably retargets. Compare to a sham control: perform the same movements without freezing A. Keep Bond stationary after release and avoid changing any other cheat. Record whether the soldier was blocked, searching, or attacking. If you cannot observe frames accurately, note ranges and uncertainty instead of inventing an exact value.

**Limitations:** one-frame RDRAM sampling cannot prove uninterrupted intra-frame Freeze; operator labels cannot measure intent; the addresses remain experimentally associated candidates, not canonical X/Z coordinates. Do not promote them to `GoldenEye.mapping` yet.
