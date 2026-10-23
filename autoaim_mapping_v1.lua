-- Launch via BizHawk: Tools > Lua Console > Open Script.
-- Run from GoldenEye.assistant repository root; no external Lua interpreter needed.
local observer=dofile("lua/autoaim_csv_v1.lua").new({
  prefix="autoaim_v1",
  interval=30
})
print("[GoldenEye.autoaim.v1] CSV sampling started (read-only); use set_phase() to label scenes.")
-- Phase labeling can be edited below before running, or through the optional events file in v2.
observer:set_phase("baseline")
observer:run()
