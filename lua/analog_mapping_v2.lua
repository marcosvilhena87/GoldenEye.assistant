-- Analog Mapping v2: raw intermediate sensitivity and input deadzone sampling.
-- No RAM access, no injection. NLua/BizHawk 2.11.1.
local M={}
local function c(v)
 local s=tostring(v==nil and "" or v)
 if s:find('[,"\r\n]') then s='"'..s:gsub('"','""')..'"' end
 return s
end
local function out(path,header,vals)
 local f=io.open(path,"r");local exists=f~=nil;if f then f:close() end
 f=assert(io.open(path,"a"));if not exists then f:write(header,"\n") end
 local a={};for i=1,#vals do a[i]=c(vals[i]) end
 f:write(table.concat(a,","),"\n");f:close()
end
local function read(port)
 for _,name in ipairs({"getimmediate","get","getwithmovie"}) do
  if joypad and joypad[name] then
   local ok,v=pcall(joypad[name],port)
   if ok and type(v)=="table" then return v,name end
  end
 end
 return nil,"none"
end
function M.new(o)
 o=o or {}
 local prefix=o.prefix or "analog_v2"
 local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
 local phase="neutral_start";local frame_last=nil;local last_x=nil;local last_y=nil
 local src_old=nil;local index=1;local interval=o.interval or 10
 local base="output/csv/"..prefix
 local inbox="output/commands/"..prefix.."_inbox/"..session
 local function frame()return emu.framecount()end
 local function diag(code,detail)
  out(base.."_diagnostics.csv","session,frame,code,detail",{session,frame(),code,detail})
 end
 local function emit(kind,src,x,y)
  local magnitude=math.sqrt(x*x+y*y)
  out(base.."_samples.csv","session,frame,phase,source,kind,x_axis,y_axis,magnitude",
   {session,frame(),phase,src,kind,x,y,string.format("%.4f",magnitude)})
 end
 local function poll()
  for _=1,20 do
   local f=io.open(string.format("%s/%06d.cmd",inbox,index),"r")
   if not f then return end
   local content=f:read("*a");f:close()
   local sid,command=content:match("^SESSION:([^\r\n]+)[\r\n]+([^\r\n]+)")
   if sid~=session then diag("SESSION_MISMATCH",sid or "")
   else
    local key,value=command:match("^([A-Z_]+):(.*)$")
    if key=="PHASE" and value~="" then
     phase=value;diag("PHASE",phase)
     -- Snapshot uses last sampled pair, not an asserted new position.
     if last_x and last_y then emit("PHASE_SNAPSHOT",src_old,last_x,last_y) end
    elseif key=="NOTE" then diag("NOTE",value)
    else diag("INVALID_COMMAND",command) end
   end
   index=index+1
  end
 end
 local obj={}
 function obj:tick()
  local fr=frame()
  if fr==frame_last then return end
  frame_last=fr
  poll()
  local v,src=read(o.port or 1)
  if not v then
   if src_old~="unavailable" then diag("SOURCE_UNAVAILABLE",src) end
   src_old="unavailable";last_x=nil;last_y=nil;return
  end
  if src~=src_old then diag("SOURCE",src);src_old=src;last_x=nil;last_y=nil end
  local x,y=v["X Axis"],v["Y Axis"]
  if type(x)~="number" or type(y)~="number" then
   diag("AXIS_UNAVAILABLE","X="..type(x)..";Y="..type(y));return
  end
  local kind=(last_x==nil and "BASELINE") or
    ((x~=last_x or y~=last_y) and "CHANGE") or
    ((fr%interval==0) and "PERIODIC") or nil
  if kind then emit(kind,src,x,y) end
  last_x=x;last_y=y
 end
 function obj:run()
  local f=assert(io.open("output/sessions/"..prefix.."_session.txt","w"))
  f:write(session,"\n");f:close()
  diag("START","input_only; interval="..interval.."; port="..tostring(o.port or 1))
  local advance=emu and (emu.frameadvance or emu.yield)
  if advance then while true do self:tick();advance() end
  elseif _G.event and _G.event.onframestart then
   _G.event.onframestart(function()self:tick()end,"goldeneye_analog_v2")
  else diag("FATAL","missing frame API") end
 end
 return obj
end
return M
