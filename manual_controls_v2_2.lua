-- GoldenEye.assistant root; update canonical export before running.
local profile=dofile("config/manual_controls_default.lua")
local detector=dofile("lua/manual_controls_v2_2.lua").new({
 port=1,profile=profile,prefix="manual_controls_v2_2"
})
print("[GoldenEye.controls] v2.2 independent trials; read-only; profile=default")
detector:run()
