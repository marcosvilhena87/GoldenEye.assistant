local M = {}
function M.new(adapter)
  return {
    enabled = false,
    fire = function()
      return false, "controller output disabled"
    end
  }
end
return M
