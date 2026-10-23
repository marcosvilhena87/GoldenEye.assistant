-- Auto-aim discovery v2: operator-labeled observations, without memory reads.
local M={}
local function field(v)
 local s=tostring(v==nil and "" or v)
 if s:find('[,"\r\n]') then s='"'..s:gsub('"','""')..'"' end
 return s
end
local function append(path,head,vals)
 local f=io.open(path,"r");local exists=f~=nil;if f then f:close() end
 f=assert(io.open(path,"a"));if not exists then f:write(head,"\n") end
 local out={};for i=1,#vals do out[i]=field(vals[i]) end
 f:write(table.concat(out,","),"\n");f:close()
end
local function controls()
 if joypad and joypad.getimmediate then
  local ok,t=pcall(joypad.getimmediate,1)
  if ok and type(t)=="table" then return t end
 end
 return nil
end
function M.new(o)
 o=o or {}
 local prefix="autoaim_v2"
 local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
 local phase="unlabeled";local n=1;local lastframe=nil;local lastbuttons=nil
 local inbox="output/commands/"..prefix.."_inbox/"..session
 local root="output/csv/"..prefix
 local function frame()return emu.framecount() end
 local function diag(code,detail)
  append(root.."_diagnostics.csv","session,frame,code,detail",{session,frame(),code,detail})
 end
 local function event(kind,detail)
  append(root.."_events.csv","session,frame,phase,event,detail",{session,frame(),phase,kind,detail})
 end
 local function poll()
  for _=1,25 do
   local f=io.open(string.format("%s/%06d.cmd",inbox,n),"r")
   if not f then break end
   local raw=f:read("*a");f:close()
   local sid,cmd=raw:match("^SESSION:([^\r\n]+)[\r\n]+([^\r\n]+)")
   if sid~=session then diag("SESSION_MISMATCH",sid or "")
   else
    local k,v=cmd:match("^([A-Z_]+):(.*)$")
    if k=="PHASE" and v~="" then phase=v;event("PHASE",v)
    elseif k=="EVENT" then event("OPERATOR",v)
    elseif k=="NOTE" then event("NOTE",v)
    else diag("INVALID_COMMAND",cmd or "") end
   end
   n=n+1
  end
 end
 local obj={}
 function obj:tick()
  local fr=frame();if lastframe==fr then return end;lastframe=fr;poll()
  local c=controls()
  if c then
   local r=tostring(c["R"] or c["P1 R"] or false)
   local z=tostring(c["Z"] or c["P1 Z"] or false)
   local state=r.."/"..z
   if state~=lastbuttons then
    event("BUTTONS_RAW","R="..r..";Z="..z..";labels_provisional")
    lastbuttons=state
   end
  end
  if fr%30==0 then
   append(root.."_samples.csv","session,frame,phase,readiness,reason",
    {session,fr,phase,"operator_only","no validated autoaim RDRAM symbols"})
  end
 end
 function obj:run()
  local f=assert(io.open("output/sessions/"..prefix.."_session.txt","w"))
  f:write(session,"\n");f:close()
  diag("START","operator-labeled; no memory reads; N64 inputs not asserted")
  while true do self:tick();emu.frameadvance() end
 end
 return obj
end
return M
