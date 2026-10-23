-- Auto-aim v2 logger; open in BizHawk Lua Console from repository root.
local observer=dofile("lua/autoaim_mapping_v2.lua").new()
print("[GoldenEye.autoaim.v2] recording operator labels; memory mapping unresolved")
observer:run()
