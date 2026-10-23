-- GoldenEye analog discovery v1; read-only NLua / BizHawk.
local M={}
local function q(v)
 local s=tostring(v==nil and "" or v)
 if s:find('[,"\r\n]') then s='"'..s:gsub('"','""')..'"' end
 return s
end
local function csv(path,header,values)
 local f=io.open(path,"r");local exists=f~=nil;if f then f:close() end
 f=assert(io.open(path,"a"))
 if not exists then f:write(header,"\n") end
 local a={};for i=1,#values do a[i]=q(values[i]) end
 f:write(table.concat(a,","),"\n");f:close()
end
local function input(port)
 for _,api in ipairs({"getimmediate","get","getwithmovie"}) do
  if joypad and joypad[api] then
   local ok,x=pcall(joypad[api],port)
   if ok and type(x)=="table" then return x,api end
  end
 end
 return nil,"none"
end
function M.new(o)
 o=o or {}
 local prefix=o.prefix or "analog_v1"
 local csv_dir=o.csv_dir or "output/csv/"
 local sessions_dir=o.sessions_dir or "output/sessions/"
 local commands_dir=o.commands_dir or "output/commands/"
 local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
 local phase="neutral"
 local previous=nil
 local source_old=nil
 local last_frame=nil
 local inbox=commands_dir..prefix.."_inbox/"..session
 local command_idx=1
 local frame=function()return emu.framecount()end
 local function diag(code,detail)
  csv(csv_dir..prefix.."_diagnostics.csv","session,frame,code,detail",{session,frame(),code,detail})
 end
 local function sample(controls,source,kind)
  csv(csv_dir..prefix.."_samples.csv","session,frame,phase,source,kind,x_axis,y_axis",
   {session,frame(),phase,source,kind,controls["X Axis"],controls["Y Axis"]})
 end
 local function command(s)
  local cmd,value=s:match("^([A-Z_]+):(.*)$")
  if cmd=="PHASE" and value~="" then
   phase=value
   diag("PHASE",value)
   if previous then sample(previous,source_old,"PHASE_SNAPSHOT") end
  elseif cmd=="NOTE" then diag("NOTE",value)
  else diag("INVALID_COMMAND",s) end
 end
 local function poll()
  for _=1,20 do
   local f=io.open(string.format("%s/%06d.cmd",inbox,command_idx),"r")
   if not f then break end
   local s=f:read("*a");f:close()
   local sid,body=s:match("^SESSION:([^\r\n]+)[\r\n]+([^\r\n]+)")
   if sid==session then command(body)
   else diag("SESSION_MISMATCH",sid or "") end
   command_idx=command_idx+1
  end
 end
 local obj={}
 function obj:tick()
  local fr=frame()
  if fr==last_frame then return end
  last_frame=fr
  poll()
  local cur,src=input(o.port or 1)
  if not cur then diag("INPUT_UNAVAILABLE",src);previous=nil;return end
  if src~=source_old then
   diag("SOURCE",src);previous=nil;source_old=src
  end
  local x,y=cur["X Axis"],cur["Y Axis"]
  if type(x)~="number" or type(y)~="number" then
   diag("AXIS_UNAVAILABLE","X="..type(x).." Y="..type(y));previous=nil;return
  end
  if not previous then sample(cur,src,"BASELINE")
  elseif x~=previous["X Axis"] or y~=previous["Y Axis"] then
   sample(cur,src,"CHANGE")
  end
  previous={["X Axis"]=x,["Y Axis"]=y}
 end
 function obj:run()
  local f=assert(io.open(sessions_dir..prefix.."_session.txt","w"))
  f:write(session,"\n");f:close()
  diag("START","read_only; axes_raw; port="..tostring(o.port or 1))
  local advance=emu and (emu.frameadvance or emu.yield)
  if advance then while true do self:tick();advance() end
  elseif _G.event and _G.event.onframestart then
   _G.event.onframestart(function()self:tick()end,"goldeneye_analog_v1")
  else diag("FATAL","No frame advancement API") end
 end
 return obj
end
return M
