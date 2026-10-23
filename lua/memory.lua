local M = {}

function M.new(snapshot, adapter, expected_rom_id, experimental)
  assert(type(snapshot) == "table", "catalog snapshot required")
  assert(type(expected_rom_id) == "string" and expected_rom_id ~= "", "ROM id required")
  if snapshot.rom_id and snapshot.rom_id ~= expected_rom_id then
    error("mapping ROM mismatch")
  end
  local by_id = {}
  for _, symbol in ipairs(snapshot.symbols or {}) do
    if symbol.rom_id == expected_rom_id and type(symbol.id) == "string" then
      if by_id[symbol.id] then error("ambiguous symbol: " .. symbol.id) end
      by_id[symbol.id] = symbol
    end
  end
  local api = {}
  function api:resolve(id)
    local symbol = by_id[id]
    if not symbol then return nil, "symbol not found for ROM" end
    local status = symbol.status
    if status ~= "validated" and not (experimental and
        (status == "reproduced" or status == "observed" or status == "candidate")) then
      return nil, "symbol not validated"
    end
    if not symbol.domain or not symbol.width_bits or not symbol.endianness
        or type(symbol.resolution) ~= "table"
        or not symbol.resolution.kind or not symbol.valid_when then
      return nil, "incomplete symbol metadata"
    end
    if symbol.resolution.kind == "unknown" then
      return nil, "unresolved address"
    end
    if symbol.resolution.kind == "absolute" and not symbol.resolution.address then
      return nil, "missing absolute address"
    end
    if symbol.resolution.kind == "pointer_chain" and
        (not symbol.resolution.base or not symbol.resolution.offsets) then
      return nil, "missing pointer chain"
    end
    return symbol
  end
  function api:read(id)
    local symbol, err = self:resolve(id)
    if not symbol then return nil, err end
    if type(adapter) ~= "table" or type(adapter.read_symbol) ~= "function" then
      return nil, "emulator adapter not configured"
    end
    -- Adapter must independently verify loaded ROM and runtime validity.
    return adapter.read_symbol(symbol)
  end
  return api
end
return M
