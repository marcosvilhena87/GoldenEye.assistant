-- Freeze Enemy Snapshot v1: read-only BizHawk Lua 5.1.
-- One selected RDRAM domain; manual GameShark switching outside this script.
local DOMAIN = "RDRAM"
local EXPECTED_SIZE = 8388608
local PREFIX = "output/"
local PHASES = {"off1", "off2", "on1", "on2", "rotate"}
local MAX_FRAMES = 72000
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,
       "Missing BizHawk memory / emu APIs")
local found = false
for _, name in ipairs(memory.getmemorydomainlist()) do
  if name == DOMAIN then found = true end
end
assert(found, "RDRAM domain unavailable: check core")
assert(memory.getmemorydomainsize(DOMAIN) == EXPECTED_SIZE,
       "Unexpected RDRAM size; do not assume address translation")
local function exists(p)
  local f = io.open(p, "rb")
  if f then f:close(); return true end
  return false
end
local function parent_ready()
  local f = io.open(PREFIX .. "sessions/freeze_enemy_write_test.tmp", "wb")
  assert(f, "Create output/sessions, output/commands and output/raw first")
  f:close()
  os.remove(PREFIX .. "sessions/freeze_enemy_write_test.tmp")
end
parent_ready()
local sid = os.date("!%Y%m%dT%H%M%SZ") .. "_" .. tostring(emu.framecount())
local stem = "freeze_enemy_v1_" .. sid
local manifest_path = PREFIX .. "sessions/" .. stem .. "_manifest.csv"
assert(not exists(manifest_path), "Refusing overwrite manifest")
local manifest = assert(io.open(manifest_path, "wb"))
manifest:write("session,frame,phase,filename,domain,bytes,reported_cheat_state,notes\n")
manifest:flush()
print("[freeze_enemy.v1] session=" .. sid)
print("[freeze_enemy.v1] RDRAM verified " .. EXPECTED_SIZE .. " bytes")
print("[freeze_enemy.v1] Manual markers: command files named output/commands/" .. stem .. "_1.txt through _5.txt")
local prior = emu.framecount()
local completed, reason = 0, "timeout"
for _ = 1, MAX_FRAMES do
  local frame = emu.framecount()
  if frame ~= prior and frame ~= prior + 1 then
    reason = "frame_discontinuity"
    break
  end
  prior = frame
  local index = completed + 1
  if index > #PHASES then reason = "complete"; break end
  local cmdpath = PREFIX .. "commands/" .. stem .. "_" .. index .. ".txt"
  if exists(cmdpath) then
    local f = assert(io.open(cmdpath, "rb"))
    local marker = f:read("*a")
    f:close()
    marker = marker:gsub("%s+$", "")
    local phase = PHASES[index]
    if marker ~= phase then reason = "bad_marker_" .. index; break end
    local outpath = PREFIX .. "raw/" .. stem .. "_" .. phase .. ".bin"
    assert(not exists(outpath), "Refusing overwrite " .. outpath)
    local out = assert(io.open(outpath, "wb"))
    local bytes, chunk = {}, {}
    local block = 4096
    for addr = 0, EXPECTED_SIZE - 1 do
      bytes[#bytes+1] = string.char(memory.read_u8(addr, DOMAIN))
      if #bytes == block then
        out:write(table.concat(bytes))
        bytes = {}
      end
    end
    if #bytes > 0 then out:write(table.concat(bytes)) end
    out:close()
    manifest:write(table.concat({sid,frame,phase,outpath,DOMAIN,EXPECTED_SIZE,
      ((phase == "off1" or phase == "off2") and "OFF" or "ON"),"manual_state_unverified"}, ","), "\n")
    manifest:flush()
    completed = index
    print("[freeze_enemy.v1] captured " .. phase .. " frame=" .. frame .. " path=" .. outpath)
    if completed == #PHASES then reason = "complete"; break end
  end
  emu.frameadvance()
end
manifest:close()
print("[freeze_enemy.v1] finished reason=" .. reason .. " count=" .. completed .. " session=" .. sid)
