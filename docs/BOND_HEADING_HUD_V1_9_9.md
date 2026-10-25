# Bond Heading v1.9.9 — Camera Pitch Candidate Validation & Temporal Signal Analysis

## Objective
The v1.9.8 capture \`20261025T213311Z_482966\` was complete (28,281 frames). The operator reported: C-Up/C-Down tilts camera vertically with hidden centered reticle; R + analog vertical tilts camera while moving a visible reticle. Its summary showed the aux pair 0D39A0/0D3D48 changing in both camera and aim vertical phases and pair 0D3998/0D3D40 changing only during aim mode vertical. However each vertical phase returned to its initial decoded float sample, and some values spanned >100 units. Those are **correlations, not pitch or reticle calibrations**.

v1.9.9 records the same read-only float32 and RAW probes as v1.9.8, retaining its command vocabulary; it adds a new offline temporal analysis over per-frame data. It also supports re-auditing the existing v1.9.8 capture without repeating gameplay.

## Components
- \`bond_heading_hud_v1_9_9.lua\` — read-only BizHawk HUD, new session files; probes 0D33F8 / 0D3400 and four auxiliary raw + experimental float32 candidates
- \`tools/send_bond_heading_hud_v1_9_9.py\` — operator phase markers, ACK required
- \`tools/audit_bond_heading_hud_v1_9_9.py\` — temporal onset, last movement, floating range, return-to-start, raw pair equality and offset range; keeps each contiguous phase occurrence separate
- \`tests/test_bond_heading_hud_v1_9_9.py\` — synthetic regression

## Re-analyze v1.9.8 evidence first
\`\`\`powershell
python -m tools.audit_bond_heading_hud_v1_9_9 20261025T213311Z_482966 --source-version v1_9_8
\`\`\`
This creates \`output/csv/bond_heading_hud_v1_9_9_20261025T213311Z_482966_temporal_audit.json\`, does not rewrite the old source data. Output creation fails if this analysis already exists (preserving audit provenance).

## New capture
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_hud_v1_9_9 -v
\`\`\`
Launch \`bond_heading_hud_v1_9_9.lua\` from repository root in BizHawk Lua Console. Send one marker at a time:
\`\`\`powershell
python -m tools.send_bond_heading_hud_v1_9_9 REFERENCE
python -m tools.send_bond_heading_hud_v1_9_9 BASELINE_STILL
python -m tools.send_bond_heading_hud_v1_9_9 CAMERA_PITCH_UP
python -m tools.send_bond_heading_hud_v1_9_9 HOLD_CAMERA_UP
python -m tools.send_bond_heading_hud_v1_9_9 CAMERA_PITCH_DOWN
python -m tools.send_bond_heading_hud_v1_9_9 HOLD_CAMERA_DOWN
python -m tools.send_bond_heading_hud_v1_9_9 AIM_MODE_PITCH_UP
python -m tools.send_bond_heading_hud_v1_9_9 HOLD_AIM_UP
python -m tools.send_bond_heading_hud_v1_9_9 AIM_MODE_PITCH_DOWN
python -m tools.send_bond_heading_hud_v1_9_9 HOLD_AIM_DOWN
python -m tools.send_bond_heading_hud_v1_9_9 STOP
\`\`\`
Wait for ACK before manually performing each intervention; make deliberate stops and hold phases of 120+ frames. The phase names do **not** prove actions occurred. No controller or RAM writes.

## Analyze
\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_hud_v1_9_9_session.txt" -Raw).Trim()
python -m tools.audit_bond_heading_hud_v1_9_9 $sid
$r=Get-Content ".\output\csv\bond_heading_hud_v1_9_9_\${sid}_temporal_audit.json" -Raw | ConvertFrom-Json
$r.complete
$r.segments | Where-Object { $_.phase -like '*PITCH*' } | ForEach-Object {
 [pscustomobject]@{
  Phase=$_.phase
  Frames=$_.frames
  X_Range=$_.signals.'0D3998'.range
  Y_Range=$_.signals.'0D39A0'.range
  X_FirstChange=$_.signals.'0D3998'.first_change_frame
  Y_FirstChange=$_.signals.'0D39A0'.first_change_frame
  Y_Returns=$_.signals.'0D39A0'.returned_to_start
  PairMatches=$_.pairs.'0D39A0_0D3D48'.identical_raw_fraction
 }
} | Format-Table -AutoSize
\`\`\`

## Interpretation limits
A transient return to the same float value is **not** proof of a camera physically returning to its origin. A pair with equal raw values on all samples may be replicated memory, and a pair with constant float offset may be an affine transform; neither proves pitch coordinates. The per-frame first/last change boundaries are bounded to the **operator-labeled phase**, not to verified button presses. The next validation gate needs an independently observed visual pitch reference and a second reproducible session.

Do not promote any address as canonical in \`GoldenEye.mapping\` yet.
