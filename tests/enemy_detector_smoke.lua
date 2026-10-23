-- Execute with Lua 5.1+ from the repository root: lua tests/enemy_detector_smoke.lua
local source = debug.getinfo(1, "S").source
assert(source:sub(1, 1) == "@", "script path unavailable")
local script_path = source:sub(2):gsub("\\", "/")
local project_root = script_path:match("^(.*)/tests/[^/]+$")
assert(project_root, "unable to resolve project root from script path")
local detector = dofile(project_root .. "/lua/enemies.lua").new({})
local function observation(entities)
  return { complete=true, source="validated_mapping",
    rom_id="fixture-rom", mapping_commit="fixture-commit", entities=entities }
end
local result, err = detector:update(observation({
  {id="guard-1",classification_status="validated",hostile=true,alive=true},
  {id="guard-2",classification_status="validated",hostile=true,alive=false},
  {id="ally-1",classification_status="validated",hostile=false,alive=true},
  {id="unknown",classification_status="candidate",hostile=true,alive=true}
}))
assert(result, err)
assert(result.enemy_count == 1 and result.enemies[1] == "guard-1")
assert(result.unknown_count == 1 and result.unknown[1] == "unknown")
assert(result.observational_only)
assert(detector:update({entities={}}) == nil)
assert(not detector.available and detector.last == nil)
assert(detector:update(observation({
  {id="duplicate",classification_status="validated",hostile=true,alive=true},
  {id="duplicate",classification_status="validated",hostile=true,alive=true}
})) == nil)
print("enemy detector v0.1 smoke tests passed")
