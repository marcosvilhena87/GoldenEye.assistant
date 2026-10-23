-- Ponto único de inicialização. Compatível com Lua 5.1 (sem require externo obrigatório).
local config = dofile("config/assistant.lua")
local function load_module(name)
  return dofile("lua/" .. name .. ".lua")
end
local snapshot = { symbols = {} }
local f = io.open("config/mapping_snapshot.lua", "r")
if f then
  f:close()
  snapshot = dofile("config/mapping_snapshot.lua")
end
if snapshot.rom_id and snapshot.rom_id ~= config.expected_rom_id then
  error("ROM incompatible with mapping snapshot")
end
local memory_api = load_module("memory").new(snapshot, nil, config.expected_rom_id, config.experimental)
local player = load_module("player").new(memory_api)
local enemies = load_module("enemies").new(memory_api)
local aim = load_module("auto_aim").new(player, enemies)
local controller = load_module("controller").new(nil)
local shot = load_module("auto_shot").new(aim, controller)
print("[GoldenEye.assistant] bootstrap ready; output disabled; mapping=" .. (snapshot.rom_id or "empty"))
return { memory = memory_api, player = player, enemies = enemies, auto_aim = aim, auto_shot = shot, controller = controller }
