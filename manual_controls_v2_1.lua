-- BizHawk Lua Console; working directory: GoldenEye.assistant
local profile=dofile("config/manual_controls_default.lua")
local detector=dofile("lua/manual_controls_v2_1.lua").new({
  port=1,prefix="manual_controls_v2_1",profile=profile
})
print("[GoldenEye.controls] v2.1 semantic recognition; read-only; profile=default")
detector:run()
