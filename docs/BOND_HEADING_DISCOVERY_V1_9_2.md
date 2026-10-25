# Bond Heading Discovery v1.9.2 — Trigonometric Cycle & Orthogonal Component Discovery

## Objective and current evidence
Probe whether \`0x0D33F8\` is a persistent heading component, sinusoidal component, or unrelated camera/weapon state. The previously observed v1.9 sequence: TURN_LEFT +1.800522 with 21 upsteps, TURN_RIGHT −1.792390, estimated full circle +0.001149, steady while translating. No heading/angle is validated. The v1.9.1 retrospective pairing \`0x0D33F8/0x0D33FC\` did **not** show unit-circle invariance (\`r²_min≈0.00001\`, \`r²_max≈0.99997\`). Do not assume \`0x0D33FC\` is the orthogonal term.

## A. Retrospective analysis of v1.9.1 (if locally captured)
\`\`\`powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_v1_9_2 -v
$sid=(Get-Content ".\output\sessions\bond_heading_v1_9_1_session.txt" -Raw).Trim()
python -m tools.analyze_bond_heading_v1_9_2 $sid --source v1.9.1
\`\`\`
This step requires a completed v1.9.1 capture. If it does not exist, proceed directly to B.

## B. New controlled capture (read only)
With GoldenEye running, start \`bond_heading_discovery_v1_9_2.lua\` in the BizHawk Lua Console from repository root. Verify RDRAM size 8 MiB. No Freeze, RAM writes or savestate load while collecting. Avoid targets, aiming and camera motion unrelated to Bond. Use a fixed visual landmark for repeatable heading estimates.

One command at a time: \`python -m tools.send_bond_heading_v1_9_2 LABEL\`. **Wait for MARKED** before making the corresponding movement. Rest 120+ frames in each HOLD phase.

1. BASELINE_STILL: fixed visual orientation.
2. TURN_LEFT_90: turn ~90° left relative to origin.
3. HOLD_90: stand still, identify landmark.
4. TURN_LEFT_180: continue ~90° left to total ~180°.
5. HOLD_180: stand still.
6. TURN_LEFT_270: continue ~90° left to total ~270°.
7. HOLD_270: stand still.
8. TURN_LEFT_360: continue ~90° left to total ~360°.
9. HOLD_360: stand still, compare visual origin.
10. TURN_RIGHT_270: ~90° right from 360°, to ~270°.
11. HOLD_R270: stand still.
12. TURN_RIGHT_180: ~90° right, to ~180°.
13. HOLD_R180: stand still.
14. TURN_RIGHT_90: ~90° right, to ~90°.
15. HOLD_R90: stand still.
16. TURN_RIGHT_0: ~90° right, back to original orientation.
17. HOLD_ORIGIN: stand still.
18. MOVE_FORWARD: move with no turn (negative control).
19. HOLD_MOVE: stand still.
20. STOP: terminate.

## C. Analyze the new session
\`\`\`powershell
$sid=(Get-Content ".\output\sessions\bond_heading_v1_9_2_session.txt" -Raw).Trim()
python -m tools.analyze_bond_heading_v1_9_2 $sid --source v1.9.2
$r=Get-Content ".\output\csv\bond_heading_v1_9_2_v1_9_2_\${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.heading_checkpoints | Format-Table -AutoSize
$r.orthogonal_candidates | Select-Object -First 15 | Format-Table -AutoSize
$r.phase_summary.TURN_LEFT_90.fields.'0x0D33F8'
\`\`\`
Candidate orthogonal component check: \`r²=x²+y²\`, computed only from TURN frames (not dominated by stationary frames). Require low r² variation **and** both fields varying appreciably. A high score alone is not proof; verify 90° phase relationship independently. Check raw/float32 interpretation, smoothness, wrap-around, clockwise/counterclockwise symmetry, constancy while translating, reproducibility, ROM/core identity.

No automatic input, no write, and no promotion to canonical GoldenEye.mapping symbols at this stage.
