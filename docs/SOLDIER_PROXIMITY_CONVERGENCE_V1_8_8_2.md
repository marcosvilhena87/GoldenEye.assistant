# Soldier proximity convergence v1.8.8.2

Use Bond approach and retreat as observational probes. This analyzer processes existing `soldier_chase_observation_v1_8_8_1.lua` captures; there is no need for a new Lua collector.

Execute one marker at a time in v1.8.8.1: BASELINE, BOND_APPROACH (Bond walks toward visually tracked Soldier #1), SOLDIER_CHASE (Bond stops, observe AI), BOND_RETREAT (Bond moves away), SOLDIER_REPOSITION, FREEZE_REQUEST_ON, FREEZE_CONFIRMED, STOP.

On completion run:
```powershell
$sid=(Get-Content ".\output\sessions\soldier_chase_v1_8_8_1_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_proximity_v1_8_8_2 $sid
$r=Get-Content ".\output\csv\soldier_proximity_v1_8_8_2_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.pairs | Where-Object { $_.approach_converged -and $_.retreat_diverged } | Select-Object -First 20 bond_offset,soldier_offset,float_format,phase_metrics | Format-List
```

Approach and retreat labels are operator-reported, not independently measured physical trajectories. This tool tests scalar |candidate-Bond - candidate-Soldier| for float32 BE/LE. Scalar difference tending to zero is only supporting evidence, not proof of common axes. Need confirmed Bond world coordinates, independent evidence about Soldier #1 identity, movement/reverse control, and cross-save replication to validate XYZ. Never promote findings to GoldenEye.mapping automatically.
