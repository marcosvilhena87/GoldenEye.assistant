local M = {}

function M.new(snapshot, adapter, expected_rom_id, experimental)
  assert(type(snapshot) == "table", "catalog snapshot required")
  assert(type(expected_rom_id) == "string" and expected_rom_id ~= "", "ROM id required")
  local symbols = snapshot.symbols or {}
  local by_id = {}
  for _, symbol in ipairs(symbols) do
    if symbol.rom_id == expected_rom_id and type(symbol.id) == "string" then
      if by_id[symbol.id] then error("ambiguous symbol: " .. symbol.id) end
      by_id[symbol.id] = symbol
    end
  end
  local api = {}
  function api:resolve(id)
    local symbol = by_id[id]
    if not symbol then return nil, "symbol not found for ROM" end
    if symbol.status ~= "validated" and not (experimental and (symbol.status == "reproduced" or symbol.status == "observed" or symbol.status == "candidate")) then
      return nil, "symbol not validated"
    end
    if not symbol.domain or not symbol.width or not symbol.endianness or not symbol.resolution or not symbol.conditions then
      return nil, "incomplete symbol metadata"
    end
    return symbol
  end
  function api:read(id)
    local symbol, err = self:resolve(id)
    if not symbol then return nil, err end
    if type(adapter) ~= "table" or type(adapter.read_symbol) ~= "function" then
      return nil, "emulator adapter not configured"
    end
    return adapter.read_symbol(symbol)
  end
  return api
end

return M
