-- Enemy Detector v0.1: observational only. No RAM addresses or controller output.
local M = {}

local function valid_id(x)
  return type(x) == "string" and x ~= ""
end

function M.new(memory_api)
  assert(memory_api, "memory API required")
  local api = { memory = memory_api, available = false, last = nil }

  -- Observations must come from a separately verified adapter. This function
  -- checks declared provenance, not the adapter's actual trustworthiness.
  function api:update(observation)
    self.available = false
    self.last = nil
    if type(observation) ~= "table" or observation.complete ~= true then
      return nil, "incomplete observation"
    end
    if observation.source ~= "validated_mapping" or
       not valid_id(observation.rom_id) or
       not valid_id(observation.mapping_commit) then
      return nil, "missing validated provenance"
    end
    if type(observation.entities) ~= "table" then
      return nil, "missing entities"
    end

    local ids, enemies, unknown = {}, {}, {}
    for i, entity in ipairs(observation.entities) do
      if type(entity) ~= "table" or not valid_id(entity.id) or ids[entity.id] then
        return nil, "invalid or duplicate entity id"
      end
      ids[entity.id] = true

      -- No implicit hostile inference from model, appearance or position.
      if entity.classification_status ~= "validated" or
         type(entity.hostile) ~= "boolean" or
         type(entity.alive) ~= "boolean" then
        unknown[#unknown + 1] = entity.id
      elseif entity.hostile and entity.alive then
        enemies[#enemies + 1] = entity.id
      end
    end
    -- Reject sparse arrays: an incomplete enumerator must never appear complete.
    local n = 0
    for k in pairs(observation.entities) do
      if type(k) ~= "number" or k < 1 or k % 1 ~= 0 then
        return nil, "malformed entities collection"
      end
      n = n + 1
    end
    if n ~= #observation.entities then
      return nil, "sparse entities collection"
    end

    table.sort(enemies)
    table.sort(unknown)
    local result = {
      rom_id = observation.rom_id,
      mapping_commit = observation.mapping_commit,
      enemies = enemies,
      unknown = unknown,
      enemy_count = #enemies,
      unknown_count = #unknown,
      observational_only = true
    }
    self.last = result
    self.available = true
    return result
  end

  return api
end

return M
