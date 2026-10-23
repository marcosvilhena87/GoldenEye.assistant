-- BizHawk Lua Console, current directory GoldenEye.assistant root.
local observer=dofile("lua/autoaim_mapping_v3_1.lua").new({prefix="autoaim_v3_1",interval=30})
print("[GoldenEye.autoaim.v3.1] recording initial state, transitions and epochs; read-only")
observer:run()
