-- GoldenEye Manual Controls Detection v1, BizHawk Lua 5.1.
-- Read only. Never calls joypad.set or writes game memory.
local M={}
local function escape(v)
  local s=tostring(v == nil and "" or v)
  if s:find('[,"\r\n]') then return '"'..s:gsub('"','""')..'"' end
  return s
end
local function csv(path,header,values)
  local exists=io.open(path,"r")
  if exists then exists:close() end
  local f=assert(io.open(path,"a"))
  if not exists then f:write(header,"\n") end
  for i=1,#values do values[i]=escape(values[i]) end
  f:write(table.concat(values,","),"\n")
  f:close()
end
local function keys(t)
  local a={}
  for k in pairs(t) do a[#a+1]=k end
  table.sort(a,function(x,y) return tostring(x)<tostring(y) end)
  return a
end
local function valstr(v)
  if type(v)=="boolean" then return v and "true" or "false" end
  if v==nil then return "" end
  return tostring(v)
end
local function read(source,port)
  if not joypad or not joypad[source] then return nil,"API_UNAVAILABLE" end
  local ok,data=pcall(joypad[source],port)
  if not ok then return nil,tostring(data) end
  if type(data)~="table" then return nil,"NON_TABLE_RESULT" end
  return data,nil
end
function M.new(opts)
  opts=opts or {}
  local prefix=opts.prefix or "manual_controls_v1"
  local port=opts.port or 1
  local session=opts.session or os.date("!%Y%m%dT%H%M%SZ")
  local previous={}
  local first=true
  local last_frame=-1
  local phase="baseline"
  local next_sample=0
  local interval=math.max(1,tonumber(opts.interval) or 1)
  local function frame() return emu and emu.framecount and emu.framecount() or -1 end
  local function log_event(source,key,kind,old,new)
    csv(prefix.."_events.csv","session,frame,phase,port,source,control,event,old_value,new_value",
      {session,frame(),phase,port,source,key,kind,valstr(old),valstr(new)})
  end
  local function diag(code,detail)
    csv(prefix.."_diagnostics.csv","session,frame,phase,code,detail",
      {session,frame(),phase,code,detail})
  end
  local function sample(source,k,v)
    csv(prefix.."_samples.csv","session,frame,phase,port,source,control,value,value_type",
      {session,frame(),phase,port,source,k,valstr(v),type(v)})
  end
  local obj={}
  function obj:set_phase(p)
    if type(p)=="string" and p~="" and p~=phase then phase=p;log_event("operator","phase","PHASE",nil,p) end
  end
  function obj:tick()
    local fr=frame()
    if fr==last_frame then return end
    last_frame=fr
    if fr<next_sample then return end
    next_sample=fr+interval
    for _,source in ipairs({"getimmediate","get","getwithmovie"}) do
      local input,err=read(source,port)
      if not input then
        if first then diag("SOURCE_UNAVAILABLE",source..": "..err) end
      else
        local old=previous[source] or {}
        local union={}
        for k in pairs(old) do union[k]=true end
        for k in pairs(input) do union[k]=true end
        for _,k in ipairs(keys(union)) do
          local v=input[k]
          local p=old[k]
          sample(source,k,v)
          if p~=v then
            local kind="CHANGE"
            if type(v)=="boolean" and type(p)=="boolean" then
              kind=v and "PRESS" or "RELEASE"
            elseif type(v)=="boolean" and p==nil then
              kind=v and "PRESS_INITIAL" or "INITIAL_OFF"
            elseif type(v)=="number" then kind="AXIS_CHANGE"
            elseif v==nil then kind="DISAPPEARED"
            end
            if not first or v==true or (type(v)=="number" and v~=0) then log_event(source,k,kind,p,v) end
          end
        end
        previous[source]=input
      end
    end
    first=false
  end
  function obj:run()
    local advance=emu and (emu.frameadvance or emu.yield)
    diag("API_PROBE","emu="..type(emu).."; frameadvance="..type(emu and emu.frameadvance).."; yield="..type(emu and emu.yield).."; event="..type(_G.event).."; onframestart="..type(_G.event and _G.event.onframestart).."; joypad="..type(joypad).."; get="..type(joypad and joypad.get))
    if advance then
      diag("START","read-only; port="..port.."; interval="..interval.."; advance API available")
      while true do self:tick(); advance() end
    end
    if _G.event and _G.event.onframestart then
      diag("INFO","CALLBACK_MODE: using event.onframestart")
      _G.event.onframestart(function() self:tick() end,"goldeneye_manual_controls_v1")
      return true
    end
    diag("FATAL","frameadvance/yield/onframestart not exposed")
    return false
  end
  return obj
end
return M
