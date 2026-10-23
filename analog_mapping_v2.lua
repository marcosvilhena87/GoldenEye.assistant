-- Run only this observer, from GoldenEye.assistant root.
local detector=dofile("lua/analog_mapping_v2.lua").new({port=1,prefix="analog_v2",interval=10})
print("[GoldenEye.analog] v2 sensitivity/deadzone probe; input only; read-only")
detector:run()
