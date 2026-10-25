# Bond Position Discovery v1 — Write-Confirmed Spatial Candidate

## Status
Operator reports that editing Cheat Search RDRAM `0x0D33EC` as unsigned word (`w u 1`) changed Bond's position. This is **operator-reported physical intervention**, not independently reproduced by the repository. No axis, scale, numerical representation or persistent physical coordinate is established. `0x0D33EA` is a neighboring address, not a confirmed second axis.

## Procedure
1. Preserve an independent savestate; verify ROM identity, N64 core, RDRAM domain, size and Cheat Search byte representation.
2. Start `bond_position_discovery_v1.lua` in BizHawk from the repository root; create `output/csv` first. In v1.0.4, the N64 core exposes `System Bus` instead of `RDRAM`. It reads the candidate offsets `0x0D33E8..0x0D33EF` via KSEG0 (`0x800D33E8..0x800D33EF`) and KSEG1 (`0xA00D33E8..0xA00D33EF`); it **never writes RAM or sends inputs**. These are hypothesized physical-memory aliases, not verified equivalence to Cheat Search. Compare values with Cheat Search before attributing any physical effect.
3. Collect separate recordings for idle, movement forward/back, pure rotation, and camera-only changes. The script's CSV `label=BASELINE` is generic; annotate external chronological intervention notes for precise times and actions. Restarting the script makes a separate session file.
4. For each controlled write experiment, restore the *same* savestate, use Cheat Search manually to change only one address by a small reversible increment, document before/after raw bytes, heading, world appearance, collision, whether displacement persists after 1/30/120 frames, and whether camera followed. Revert by restoring state. Do not simultaneously alter neighboring addresses.
5. Repeat `0x0D33EC` first; optionally test `0x0D33EA` in independent resets. Compare `u16 BE/LE`, full aligned `u32` and byte effects before assuming word boundaries.
6. Repeat from a fresh gameplay session and verify ROM/core consistency. Physical movement and heading require independent visual/operator ground truth; CSV changes alone do not validate coordinates.

## Output
`output/csv/bond_position_v1_<UTC>.csv` columns: session, frame, phase, offset_hex, kseg0_hex, kseg1_hex, kseg0_u16_be, kseg0_u16_le, kseg1_u16_be, kseg1_u16_le, alias_equal, kseg0_changed. Phase is UNMARKED: annotate intervention frames outside the capture. Raw bytes preserve interpretation alternatives. The script has no STOP mechanism: close it in Lua Console; CSV flushes every 60 frames.

## Promotion gate
This candidate stays diagnostic read-only. Promote only after independent reproduction of controlled single-address write, positive/negative controls, axis disambiguation, persistence, dynamic-address stability, ROM/core proof and explicit evidence provenance. Do not connect to automatic movement or `lua/player.lua` yet.

## BizHawk N64 domain diagnostics (2026-10-24)
User's Lua Console returned ROM, hardware registers, save memory, System Bus, CPU registers, but no RDRAM. v1.0.4 switches to System Bus KSEG0/KSEG1 offsets. Compare raw bytes and changes with Cheat Search before assuming aliases or game coordinate semantics; KSEG mirror equality alone does not prove the game interprets this as a position. If reads fail, preserve error logs; do not write via Lua.
