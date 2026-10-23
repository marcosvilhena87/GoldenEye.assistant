# Auto-Aim Mapping v3.1 — initial state and experimental quality

This version is independent from v3. No RAM addresses, game-memory reading/writing or auto-fire.

**Important correction:** A1 starts with auto-aim *already enabled*, so there is no intervention required in A1. Instead the operator supplies an `INITIAL enabled` annotation, separately from in-experiment interventions. This is still a human-declared setting, not a memory-verified state.

## Start

Close v3 and open `autoaim_mapping_v3_1.lua` in the BizHawk Lua Console from the repository root. Prepare output folders with `python .\tools\prepare_output.py`.

### A/B/A protocol

Run each command at the appropriate moment, *not as one batch*. Declare initial state before or during A1, without changing the game's already-enabled option:

```powershell
python .\tools\send_autoaim_v3_1.py INITIAL enabled
python .\tools\send_autoaim_v3_1.py PHASE aba_enabled_1
python .\tools\send_autoaim_v3_1.py EVENT aim_shift_observed
```

Switch assistance **off in the game**, then annotate the actual intervention:

```powershell
python .\tools\send_autoaim_v3_1.py PHASE aba_disabled
python .\tools\send_autoaim_v3_1.py INTERVENTION autoaim_disabled_in_menu
python .\tools\send_autoaim_v3_1.py EVENT no_aim_shift_observed
```

Switch assistance back **on**, and annotate accordingly:

```powershell
python .\tools\send_autoaim_v3_1.py PHASE aba_enabled_2
python .\tools\send_autoaim_v3_1.py INTERVENTION autoaim_enabled_in_menu
python .\tools\send_autoaim_v3_1.py EVENT aim_shift_observed
```

Only report the events that actually occurred. Mark manual aiming as `INTERVENTION manual_aim_R` and shooting as `INTERVENTION fire_Z`. Record `INTERVENTION savestate_loaded` when applicable. Frame regressions increment `epoch`, cause undetermined.

## Analyze

```powershell
python .\tools\report_autoaim_v3_1.py
Get-Content .\output\csv\autoaim_v3_1_diagnostics.csv -Tail 20
```

Quality checker verifies: initial state declared as enabled, one outcome per A/B/A phase, interventions for B/A2, missing phases, multiple epochs, and tentative R/Z presses. A1 requires **no intervention**. Flags describe annotation completeness, **not causal validation**.

To verify frame-regression handling, run a separate controlled savestate rewind and check for `FRAME_REGRESSION` and incremented epoch. Do not confuse new sessions with savestate rewinds. Source of truth for memory remains GoldenEye.mapping; do not invent addresses.
