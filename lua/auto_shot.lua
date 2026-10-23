local M = {}
function M.new(auto_aim, controller)
  return {
    enabled = false,
    evaluate = function()
      return false, "auto-shot disabled: no validated target and fire predicates"
    end
  }
end
return M
