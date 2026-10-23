-- GoldenEye Auto-Aim Mapping v3. Observer only: no RDRAM or joypad writes.
local M={}
local function csvfield(v)
 local s=tostring(v==nil and "" or v)
 if s:find('[,"\r\n]') then return '"'..s:gsub('"','""')..'"' end
 return s
end
local function append(path,header,values)
 local f=io.open(path,"r");local exists=f~=nil;if f then f:close() end
 f=assert(io.open(path,"a"));if not exists then f:write(header,"\n") end
 local t={};for i=1,#values do t[i]=csvfield(values[i]) end
 f:write(table.concat(t,","),"\n");f:close()
end
local function input()
 if joypad and type(joypad.getimmediate)=="function" then
  local ok,data=pcall(joypad.getimmediate,1)
  if ok and type(data)=="table" then return data end
 end
 return nil
end
local function bool(v)
 return v==true or v==1 or v=="True" or v=="true"
end
function M.new(options)
 local o=options or {}
 local prefix=o.prefix or "autoaim_v3"
 local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
 local root="output/csv/"..prefix
 local inbox="output/commands/"..prefix.."_inbox/"..session
 local interval=o.interval or 30
 local epoch=0;local last_frame=nil;local phase="unlabeled"
 local cmd_idx=1;local last_r=nil;local last_z=nil
 local function frame() return emu.framecount() end
 local function diag(code,detail)
  append(root.."_diagnostics.csv","session,epoch,frame,code,detail",
   {session,epoch,frame(),code,detail})
 end
 local function event(kind,detail,command_id)
  append(root.."_events.csv","session,epoch,frame,phase,event,detail,command_id",
   {session,epoch,frame(),phase,kind,detail,command_id or ""})
 end
 local function poll()
  for _=1,25 do
   local file=io.open(string.format("%s/%06d.cmd",inbox,cmd_idx),"r")
   if not file then break end
   local raw=file:read("*a");file:close()
   local sid,cmd=raw:match("^SESSION:([^\r\n]+)[\r\n]+([^\r\n]+)")
   if sid~=session then diag("SESSION_MISMATCH",sid or "")
   else
    local key,value=(cmd or ""):match("^([A-Z_]+):(.*)$")
    if key=="PHASE" and value~="" then phase=value;event("PHASE",value,cmd_idx)
    elseif key=="EVENT" and value~="" then event("OPERATOR",value,cmd_idx)
    elseif key=="NOTE" and value~="" then event("NOTE",value,cmd_idx)
    elseif key=="INTERVENTION" and value~="" then event("INTERVENTION_OPERATOR",value,cmd_idx)
    else diag("INVALID_COMMAND",cmd or "") end
   end
   cmd_idx=cmd_idx+1
  end
 end
 local obj={}
 function obj:tick()
  local fr=frame()
  if fr==last_frame then return end
  if last_frame~=nil and fr<last_frame then
   local previous=last_frame
   epoch=epoch+1
   -- Explicit discontinuity; do not infer cause (savestate, rewind, reset).
   diag("FRAME_REGRESSION","previous="..previous..";current="..fr..";cause=unknown")
   event("EPOCH_START","frame_regression_from="..previous)
   last_r=nil;last_z=nil
  end
  last_frame=fr
  poll()
  local c=input()
  if c then
   -- These are raw tentative API keys, not validated N64 button identities.
   local r=bool(c["R"] or c["P1 R"])
   local z=bool(c["Z"] or c["P1 Z"])
   if last_r==nil or r~=last_r then
    event("RAW_R",r and "pressed" or "released")
    last_r=r
   end
   if last_z==nil or z~=last_z then
    event("RAW_Z",z and "pressed" or "released")
    last_z=z
   end
  end
  if fr%interval==0 then
   append(root.."_samples.csv","session,epoch,frame,phase,status,reason",
    {session,epoch,fr,phase,"operator_only","no validated autoaim memory symbol"})
  end
 end
 function obj:run()
  local f=assert(io.open("output/sessions/"..prefix.."_session.txt","w"))
  f:write(session,"\n");f:close()
  diag("START","read_only; epoch tracking; source=operator; interval="..interval)
  while true do self:tick();emu.frameadvance() end
 end
 return obj
end
return M
