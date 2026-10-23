-- Launch from repository root in BizHawk Lua Console.
local detector=dofile("lua/manual_controls_v1.lua").new({port=1,interval=1})
print("[GoldenEye.controls] v1 manual input CSV recorder started; port=1")
detector:run()
