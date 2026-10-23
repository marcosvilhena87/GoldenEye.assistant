local M = {}
function M.new(memory_api)
  assert(memory_api, "memory API required")
  return { memory = memory_api, available = false }
end
return M
