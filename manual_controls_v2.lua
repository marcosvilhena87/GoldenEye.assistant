-- BizHawk Lua Console, working directory: GoldenEye.assistant
-- Stop v1 before running v2. No control injection.
local detector=dofile("lua/manual_controls_v2.lua").new({port=1,prefix="manual_controls_v2"})
print("[GoldenEye.controls] Recognition v2 started; read-only; command file=manual_controls_v2_commands.txt")
detector:run()
