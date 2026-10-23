-- GoldenEye Auto-Aim Mapping v1: passive CSV observer (Lua 5.1 / BizHawk).
-- No guessed addresses, writes to game memory, or injected inputs.
local M = {}
local function csv(v)
  if v == nil then return "" end
  local s=tostring(v)
  if s:find('[,"\r\n]') then return '"'..s:gsub('"','""')..'"' end
  return s
end
local function append(path, header, values)
  local f=io.open(path,"r")
  local exists=f~=nil
  if f then f:close() end
  f=assert(io.open(path,"a"))
  if not exists then f:write(header,"\n") end
  local count=1
  for _ in header:gmatch(",") do count=count+1 end
  for i=1,count do values[i]=csv(values[i]) end
  f:write(table.concat(values,","),"\n")
  f:close()
end
local SAMPLE_HEADER="session,frame,phase,autoaim_enabled,target_x,target_y,aim_x,aim_y,status,reason"
local EVENT_HEADER="session,frame,event,phase,detail"
local DIAG_HEADER="session,frame,severity,code,detail"
local function framecount()
  return emu and emu.framecount and emu.framecount() or -1
end
function M.new(opts)
  opts=opts or {}
  local prefix=opts.prefix or "autoaim_v1"
  local session=opts.session or os.date("!%Y%m%dT%H%M%SZ")
  local interval=math.max(1,tonumber(opts.interval) or 30)
  local phase="unlabeled"
  local last_status=nil
  local last_phase=nil
  local next_frame=0
  local command_cursor=0
  local commands_path=prefix.."_commands.txt"
  local resolver=opts.reader -- optional: function returns values/status from validated mapping only
  local function event(name,detail)
    append(prefix.."_events.csv",EVENT_HEADER,{session,framecount(),name,phase,detail or ""})
  end
  local function diagnostic(level,code,detail)
    append(prefix.."_diagnostics.csv",DIAG_HEADER,{session,framecount(),level,code,detail or ""})
  end
  local obj={}
  function obj:set_phase(value)
    if type(value)~="string" or value=="" then return false end
    if phase~=value then phase=value; event("PHASE",value) end
    return true
  end
  function obj:mark(name,detail) event(name,detail) end
  function obj:tick()
    local cmd=io.open(commands_path,"r")
    if cmd then
      local bytes=cmd:seek("end") or 0
      if bytes<command_cursor then command_cursor=0 end
      cmd:seek("set",command_cursor)
      while true do
        local line=cmd:read("*l")
        if not line then break end
        local newpos=cmd:seek()
        if line:match("^PHASE:") then
          self:set_phase(line:sub(7))
        elseif line:match("^EVENT:") then
          event("OPERATOR",line:sub(7))
        elseif line:match("^NOTE:") then
          event("NOTE",line:sub(6))
        elseif line~="" then
          diagnostic("WARN","INVALID_COMMAND",line)
        end
        command_cursor=newpos
      end
      cmd:close()
    end
    local frame=framecount()
    if frame<next_frame then return end
    next_frame=frame+interval
    local info={status="unresolved",reason="no validated mapping reader"}
    if type(resolver)=="function" then
      local ok,result=pcall(resolver)
      if ok and type(result)=="table" then
        info=result
        if info.status==nil then info.status="unresolved" end
      else
        info={status="error",reason=ok and "reader did not return table" or tostring(result)}
      end
    end
    append(prefix.."_samples.csv",SAMPLE_HEADER,{
      session,frame,phase,info.autoaim_enabled,info.target_x,info.target_y,
      info.aim_x,info.aim_y,info.status,info.reason
    })
    if info.status~=last_status then
      diagnostic(info.status=="error" and "ERROR" or "INFO","STATUS_CHANGE",info.status..": "..(info.reason or ""))
      last_status=info.status
    end
  end
  function obj:run()
    if not (emu and type(emu.frameadvance)=="function") then
      diagnostic("ERROR","NO_EMULATOR","BizHawk emu.frameadvance unavailable")
      return false
    end
    diagnostic("INFO","START","read-only; frames interval="..interval)
    while true do self:tick(); emu.frameadvance() end
  end
  event("START","observer v1")
  return obj
end
return M
