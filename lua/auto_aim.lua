local M = {}
function M.new(player, enemies)
  return {
    available = false,
    evaluate = function()
      return nil, "auto-aim not validated"
    end
  }
end
return M
