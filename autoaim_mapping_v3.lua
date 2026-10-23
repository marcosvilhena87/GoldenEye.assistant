-- Launch from GoldenEye.assistant repository root in BizHawk Lua Console.
local observer=dofile("lua/autoaim_mapping_v3.lua").new({prefix="autoaim_v3",interval=30})
print("[GoldenEye.autoaim.v3] observer running; epochs and operator interventions; read-only")
observer:run()
