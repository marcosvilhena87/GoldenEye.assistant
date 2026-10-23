-- BizHawk Lua Console; run from GoldenEye.assistant root.
local profile=dofile("config/manual_controls_default.lua")
local detector=dofile("lua/manual_controls_v2_2_1.lua").new({
 port=1,profile=profile,prefix="manual_controls_v2_2_1"
})
print("[GoldenEye.controls] v2.2.1 Session Safety; read-only; profile=default")
detector:run()
