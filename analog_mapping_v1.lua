-- Start from GoldenEye.assistant root; do not run alongside other logger scripts.
local observer=dofile("lua/analog_mapping_v1.lua").new({port=1,prefix="analog_v1"})
print("[GoldenEye.analog] analog mapping v1 started; read-only")
observer:run()
