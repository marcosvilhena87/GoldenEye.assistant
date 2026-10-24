# Horizontal Correction Discovery v1.5.1 — Timeline Integrity

Patch of v1.5; old files and session artifacts remain unchanged.

## What changed
- Every timeline row and transition has a monotonic `sample_index` (Lua iteration, starting at 1). Marker records also have the current `sample_index`.
- `emu.framecount()` must increase by exactly 1 between consecutive samples. On jump or rollback, the collector **stops before recording the discontinuous frame**, writes `*_discontinuities.csv` with previous/current frame and active action, and records `reason=timeline_discontinuity` and the still-open action in termination.csv. No false END is synthesized.
- STOP, frame limit, and invalid-marker reasons remain distinct. Commands created after termination are rejected by the sender when the termination CSV has a data row.
- Analyzer brackets by `sample_index`, not frame number, and rejects frame gaps, sample gaps, incomplete actions, or reordered markers. No event comparison crosses a discontinuity.
- Unverified camera heading remains nil. Everything read-only; no changes to canonical mapping.

## Start a fresh v1.5.1 session
1. `git pull --ff-only origin main`
2. `python -m unittest discover -s tests -v`
3. Set `DOMAIN="RDRAM"` and `EXPECTED_SIZE=8388608` in `horizontal_correction_discovery_v1_5_1.lua` **only after verifying the emulator domain**.
4. Launch the v1.5.1 Lua script from the repository root within BizHawk. Use a **new** session.
5. Run `python .\tools\send_horizontal_v1_5_1.py BEGIN_FIXED_NO_TARGET`; **wait for** `[horizontal.v1.5.1] marked ...`, perform observed intervention, then `END_FIXED_NO_TARGET`. Do not send multiple queued commands without acknowledgement.
6. Repeat v1.5 experimental action names for fixed aim and turn controls. Do not load savestates within a session; if one occurs, the collector should stop cleanly.
7. Send STOP only after completing the current bracket, and confirm acknowledgement.
8. Analyze once, **after** session is complete (output refuses overwrite):
```powershell
$session = (Get-Content .\output\sessions\horizontal_v1_5_1_session.txt -Raw).Trim()
python .\tools\analyze_horizontal_v1_5_1.py $session
Import-Csv ".\output\csv\horizontal_v1_5_1_${session}_termination.csv" | Format-Table
Import-Csv ".\output\csv\horizontal_v1_5_1_${session}_discontinuities.csv" | Format-Table
Import-Csv ".\output\csv\horizontal_v1_5_1_${session}_calibration_audit.csv" | Select-Object action,offset_hex,begin_sample_index,end_sample_index,changes | Format-Table -AutoSize
```

A completed FIXED_NO_TARGET control in v1.5 session `20261023T235634Z_2677` is preserved, but that earlier session experienced a frame rollback `36461 -> 2342` and terminated at frame limit with FIXED_AIM_LEFT open; it must not be silently reinterpreted as a continuous capture.

No camera orientation, weapon angle, data representation, correction sign/scale, or automatic rotation is validated by this release.
