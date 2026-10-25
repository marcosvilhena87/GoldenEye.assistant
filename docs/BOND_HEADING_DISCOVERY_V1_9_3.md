# Bond Heading v1.9.3 — Angular Reconstruction & Heading Calibration

## Scope
This release reconstructs a **mathematical candidate angle** from the observed approximately unit-length float32 big-endian pair:

- X = RDRAM \`0x0D33F8\`
- Y = RDRAM \`0x0D3400\`

The 14,450-frame v1.9.2 session \`20261025T194512Z_142068\` recorded 7,744 turning frames with \`x²+y²\` between 0.999999622 and 1.000000475. This supports a normalized 2D vector hypothesis. It does **not** establish the game's heading convention, zero axis, camera vs body vs gun, or an independent physical angle.

The analyzer derives \`theta_deg = degrees(atan2(y,x))\`, wraps deltas to [-180,180), accumulates unwrapped differences only between adjacent valid frames, separates left/right phases, lists hold checkpoints and compares their candidate angles to the operator's **approximate** 90/180/270/360° labels under either sign convention. The estimates are diagnostic only; no independent angle calibration is claimed.

## Installation and retrospective audit
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_v1_9_3 -v
$sid="20261025T194512Z_142068"
python -m tools.analyze_bond_heading_v1_9_3 $sid

$r=Get-Content ".\output\csv\bond_heading_v1_9_3_\${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.checkpoints | Format-Table -AutoSize
$r.nominal_comparisons | Format-Table -AutoSize
$r.phase_stats | Format-List
\`\`\`

Per-frame output: \`output/csv/bond_heading_v1_9_3_<sid>_angles.csv\`.
Analysis output: \`output/csv/bond_heading_v1_9_3_<sid>_analysis.json\`.
Both refuse overwrites.

## Test interpretation
- \`phase_stats\`: counts, vector norm error, sign of instantaneous angular steps, integrated turn and largest jump.
- \`checkpoints\`: candidate heading at the end of each stationary phase relative to baseline.
- \`nominal_comparisons\`: hypothetical errors in either sign convention relative to manually assigned quadrants. **Not** independent angular measurement.
- \`unwrapped_deg\`: cumulative angle within uninterrupted valid sequences (resets when norm invalid or timeline discontinuous).
- Large absolute deltas indicate undersampling, abrupt camera adjustment or source instability; do not automatically reinterpret as a full rotation.

## Next physical calibration (not yet implemented)
1. Pick a distinctive fixed scene landmark and a Bond initial location.
2. Record orientation from the landmark independently of RAM; repeat several times.
3. Compare left and right turns of visually checked 90°, 180°, 270° and 360°.
4. Confirm stable candidate angle while walking without turning and changing weapon/aim without body turn.
5. Repeat in a fresh game session and verify ROM SHA-256, N64 core, memory domain/endian and offsets.
6. Only after independent calibration consider identifying the sign and zero axis as the game-world heading. Until then, \`GoldenEye.mapping\` remains unchanged and Auto-Align remains disabled.

No Lua writing and no controller automation in v1.9.3.
