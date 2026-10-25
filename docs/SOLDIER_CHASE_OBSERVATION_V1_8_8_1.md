# Soldier Coordinate v1.8.8.1 — Uncontrolled Chase Observation

This corrects the invalid assumption in v1.8.8 that the operator can direct enemy soldiers. Only Bond is controlled; the Soldier #1 is visually tracked, with optional enemy Freeze.

Run `soldier_chase_observation_v1_8_8_1.lua` in BizHawk from repository root; ensure 8MiB RDRAM and directories `output/{csv,commands,sessions}`. Send each stage using `python -m tools.send_soldier_chase_v1_8_8_1 LABEL`; wait for MARKED, observe at least 120 frames between markers and visually verify the soldier.

Markers: BASELINE; BOND_APPROACH (approach soldier), SOLDIER_CHASE (stop Bond and observe pursuit), BOND_RETREAT (retreat Bond), SOLDIER_REPOSITION (hold Bond still and watch AI movement), FREEZE_REQUEST_ON (enable cheat), FREEZE_CONFIRMED (confirm visually), STOP.

After DONE stop:
```powershell
$sid=(Get-Content ".\output\sessions\soldier_chase_v1_8_8_1_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_chase_v1_8_8_1 $sid
$r=Get-Content ".\output\csv\soldier_chase_v1_8_8_1_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.capture_complete
$r.fields | Select-Object -First 20 | Format-Table -AutoSize
$r.duplicate_pairs | Format-Table -AutoSize
```

This protocol finds phase-linked changes and duplicate bytes; it cannot identify X/Z signs without independent observed direction or prove Soldier #1 RAM identity. Do not promote a symbol to GoldenEye.mapping based on these results alone.
