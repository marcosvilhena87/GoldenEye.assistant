-- Manual Controls Recognition v2.1 — read-only, Lua 5.1 / NLua BizHawk.
-- Raw names preserved. Actions supplied by operator are hypotheses, not confirmed mappings.
local M={}
local function str(v)
 if v==nil then return "" end
 if type(v)=="boolean" then return v and "true" or "false" end
 return tostring(v)
end
local function cell(v)
 local s=str(v)
 if s:find('[,"\r\n]') then s='"'..s:gsub('"','""')..'"' end
 return s
end
local function write(path,header,fields)
 local f=io.open(path,"r"); local present=f~=nil; if f then f:close() end
 f=assert(io.open(path,"a"));if not present then f:write(header,"\n") end
 local n=1;for _ in header:gmatch(",") do n=n+1 end
 local out={};for i=1,n do out[i]=cell(fields[i]) end
 f:write(table.concat(out,","),"\n");f:close()
end
local function read_input(port)
 if not joypad then return nil,"NO_JOYPAD" end
 for _,name in ipairs({"getimmediate","get","getwithmovie"}) do
  if joypad[name] then
   local ok,res=pcall(joypad[name],port)
   if ok and type(res)=="table" then return res,name end
  end
 end
 return nil,"NO_READABLE_SOURCE"
end
local function sorted_keys(t)
 local a={};for k in pairs(t) do a[#a+1]=k end
 table.sort(a,function(x,y) return tostring(x)<tostring(y) end);return a
end
function M.new(o)
 o=o or {}
 local prefix=o.prefix or "manual_controls_v2_1"
 local session=o.session or os.date("!%Y%m%dT%H%M%SZ")
 local port=o.port or 1
 local phase="baseline"; local action="unlabeled";local expected=""
 local last_frame=nil;local previous=nil;local last_source=nil;local cursor=0
 local command_path=prefix.."_commands.txt"
 local profile=o.profile
 assert(type(profile)=="table" and profile.profile=="default" and type(profile.mappings)=="table","Canonical profile required")
 local by_button={}
 for _,item in ipairs(profile.mappings) do by_button[item.button]=item.action_id end
 local diag
 local trial_id=0
 local pending=nil
 local function validation(result,observed,notes)
  if not pending then diag("NO_PENDING_TRIAL",result);return end
  local semantic=(observed~="" and observed or "unobserved")
  local match="unknown"
  if result=="yes" then match=semantic==pending.expected_action and "yes" or "no"
  elseif result=="no" then match="no" end
  local status=(result=="yes" and match=="yes") and "operator_observed" or
    (result=="unknown" and "inconclusive" or "contradicted")
  write(prefix.."_validation.csv",
    "session,trial_id,press_frame,report_frame,phase,profile,source,control,expected_action,observed_action,result,match,status,notes",
    {session,pending.id,pending.frame,frame(),pending.phase,profile.profile,pending.source,pending.control,
    pending.expected_action,semantic,result,match,status,notes})
  pending=nil
 end
 local function frame()
  if emu and emu.framecount then
   local ok,v=pcall(emu.framecount);if ok then return v end
  end
  return -1
 end
 local function evt(kind,control,old,new,source)
  write(prefix.."_events.csv","session,frame,phase,action,port,source,control,event,old_value,new_value",
   {session,frame(),phase,action,port,source or "",control or "",kind,old,new})
 end
 diag=function(code,detail)
  write(prefix.."_diagnostics.csv","session,frame,code,detail",
   {session,frame(),code,detail})
 end
 local function annotation(kind,detail)
  write(prefix.."_annotations.csv","session,frame,phase,action,expected_control,kind,detail",
   {session,frame(),phase,action,expected,kind,detail or ""})
 end
 local function control_line(line)
  local cmd,value=line:match("^%s*([A-Z_]+)%s*:%s*(.-)%s*$")
  if not cmd then diag("INVALID_COMMAND",line);return end
  if cmd=="PHASE" and value~="" then
   phase=value;annotation("PHASE",value)
  elseif cmd=="ACTION" and value~="" then
   action=value;annotation("ACTION",value)
  elseif cmd=="EXPECT" then expected=value;annotation("EXPECT",value)
  elseif cmd=="EVENT" or cmd=="NOTE" then annotation(cmd,value)
  elseif cmd=="OBSERVED" then
   if pending then pending.observed=value;annotation("OBSERVED",value)
   else diag("NO_PENDING_TRIAL","OBSERVED:"..value) end
  elseif cmd=="RESULT" then
   local result=value:lower()
   if result=="yes" or result=="no" or result=="unknown" then
    validation(result,pending and (pending.observed or "") or "","operator response")
   else diag("INVALID_RESULT",value) end
  elseif cmd=="RESET" then
   action="unlabeled";expected="";phase="baseline";pending=nil;annotation("RESET","")
  else diag("INVALID_COMMAND",line) end
 end
 local function poll_commands()
  local f=io.open(command_path,"r");if not f then return end
  local length=f:seek("end") or 0
  if length<cursor then cursor=0 end
  f:seek("set",cursor)
  while true do
   local start=f:seek()
   local line=f:read("*l")
   if not line then break end
   -- Only complete newline-terminated records are consumed.
   local finish=f:seek()
   if finish>length then f:seek("set",start);break end
   cursor=finish
   if line~="" then control_line(line) end
  end
  f:close()
 end
 local obj={}
 function obj:tick()
  local fr=frame()
  if last_frame==fr then return end
  last_frame=fr
  poll_commands()
  local cur,src=read_input(port)
  if not cur then
   if last_source~="unavailable" then diag("SOURCE_UNAVAILABLE",src) end
   last_source="unavailable";previous=nil;return
  end
  if src~=last_source then diag("SOURCE",src);previous=nil;last_source=src end
  if previous then
   local union={};for k in pairs(previous) do union[k]=true end
   for k in pairs(cur) do union[k]=true end
   for _,key in ipairs(sorted_keys(union)) do
    local a,b=previous[key],cur[key]
    if a~=b then
     local kind="CHANGE"
     if type(a)=="boolean" and type(b)=="boolean" then
      kind=b and "PRESS" or "RELEASE"
     elseif type(b)=="number" then kind="AXIS_CHANGE"
     elseif b==nil then kind="DISAPPEARED" end
     evt(kind,key,str(a),str(b),src)
     if kind=="PRESS" and by_button[key] then
      if pending then validation("unknown",pending.observed or "","superseded by new press") end
      trial_id=trial_id+1
      pending={id=trial_id,frame=fr,phase=phase,source=src,control=key,
        expected_action=by_button[key],observed=""}
      annotation("TRIAL_OPEN",key.." => "..pending.expected_action)
     end
    end
   end
  else
   local n=0;for _ in pairs(cur) do n=n+1 end
   diag("BASELINE","controls="..n)
  end
  previous=cur
 end
 function obj:run()
  diag("API_PROBE","frameadvance="..type(emu and emu.frameadvance).."; yield="..type(emu and emu.yield).."; event.onframestart="..type(_G.event and _G.event.onframestart))
  annotation("START","semantic validation; canonical profile="..profile.profile.."; no RAM")
  local advance=emu and (emu.frameadvance or emu.yield)
  if advance then
   diag("START","loop");while true do self:tick();advance() end
  elseif _G.event and _G.event.onframestart then
   diag("START","callback")
   _G.event.onframestart(function() self:tick() end,"goldeneye_manual_controls_v2_1")
  else diag("FATAL","no frame callback or advance available");return false end
  return true
 end
 return obj
end
return M
