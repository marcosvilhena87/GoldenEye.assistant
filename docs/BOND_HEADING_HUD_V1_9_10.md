# Bond Heading v1.9.10 — Pitch Signal Correlation & Temporal Alignment

Offline analysis of historical v1.9.8 or v1.9.9 recordings. Fresh sessions can continue using the v1.9.9 read-only Lua HUD.

It checks RAW identity of 0D3998/0D3D40 and 0D39A0/0D3D48, then compares first differences using Pearson correlation and signed frame lags. Positive lag means the second field changes later. Flat signals give undefined correlation; correlation is never evidence of causal or physical camera/reticle meaning.

## Run

```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_10 -v
python -m tools.audit_bond_heading_hud_v1_9_10 20261025T213311Z_482966 --source-version v1_9_8 --max-lag 120
$sid="20261025T213311Z_482966"
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_10_${sid}_correlation.json" -Raw | ConvertFrom-Json
$r.historical_complete
$r.vertical_interventions | ForEach-Object {
 [pscustomobject]@{
  Phase=$_.phase
  Frames=$_.frames
  RawEqual=$_.pairs.'0D39A0_0D3D48'.raw_equal_fraction
  PairLag=$_.pairs.'0D39A0_0D3D48'.lag_scan.best.lag_frames
  PairPearson=$_.pairs.'0D39A0_0D3D48'.lag_scan.best.pearson
  CrossLag=$_.pairs.'0D3998_0D39A0'.lag_scan.best.lag_frames
 }
} | Format-Table -AutoSize
```

An earlier difference of 320 or 222 frames between first changes within phase labels is not by itself the correlation lag. The exhaustive search can overfit; replicate in fresh captures. This tool neither writes game RAM nor drives controller inputs. No promotion to GoldenEye.mapping is supported.
