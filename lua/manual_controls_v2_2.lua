-- GoldenEye Manual Controls Recognition v2.2 — independent trials; Lua 5.1 / BizHawk NLua.
-- Read-only: no memory writes and no input injection.
local M={}
local function asstr(v)
 if v==nil then return "" end
 if type(v)=="boolean" then return v and "true" or "false" end
 return tostring(v)
end
local function csv(v)
 local s=asstr(v)
 if s:find('[,"\r\n]') then return '"'..s:gsub('"','""')..'"' end
 return s
end
local function append(path,header,values)
 local f=io.open(path,"r");local exists=f~=nil;if f then f:close() end
 f=assert(io.open(path,"a"))
 if not exists then f:write(header,"\n") end
 local out={}
 for i=1,select(2,header:gsub(",",""))+1 do out[i]=csv(values[i]) end
 f:write(table.concat(out,","),"\n");f:close()
end
local function keys(t)
 local r={};for k in pairs(t) do r[#r+1]=k end
 table.sort(r,function(a,b)return tostring(a)<tostring(b) end);return r
end
local function inputs(port)
 if not joypad then return nil,"NO_JOYPAD" end
 for _,api in ipairs({"getimmediate","get","getwithmovie"}) do
  if joypad[api] then
   local ok,v=pcall(joypad[api],port)
   if ok and type(v)=="table" then return v,api end
  end
 end
 return nil,"NO_INPUT_API"
end
function M.new(opts)
 local o=opts or {}
 local prefix=o.prefix or "manual_controls_v2_2"
 local port=o.port or 1
 local profile=assert(o.profile,"Canonical profile export missing")
 assert(profile.profile=="default" and type(profile.mappings)=="table","Invalid profile")
 local mapping={}
 for _,m in ipairs(profile.mappings) do
  assert(type(m.button)=="string" and type(m.action_id)=="string")
  mapping[m.button]=m.action_id
 end
 local session=os.date("!%Y%m%dT%H%M%SZ")
 local phase="baseline"
 local last_frame=nil;local old=nil;local old_source=nil
 local trials={};local trial_num=0
 local queue=o.queue or "manual_controls_v2_2_inbox"
 local next_command=1
 local function frame()
  if emu and emu.framecount then
   local ok,v=pcall(emu.framecount)
   if ok then return v end
  end
  return -1
 end
 local function diagnostics(code,detail)
  append(prefix.."_diagnostics.csv","session,frame,code,detail",{session,frame(),code,detail})
 end
 local function annotate(kind,id,detail)
  append(prefix.."_annotations.csv","session,frame,phase,trial_id,kind,detail",
   {session,frame(),phase,id,kind,detail})
 end
 local function pending_report()
  local f=assert(io.open(prefix.."_pending.csv","w"))
  f:write("session,trial_id,press_frame,phase,control,expected_action,observed_action\n")
  for i=1,trial_num do
   local t=trials[i]
   if t and not t.closed then
    f:write(table.concat({csv(session),csv(i),csv(t.frame),csv(t.phase),csv(t.control),
     csv(t.expected),csv(t.observed)} ,","),"\n")
   end
  end
  f:close()
 end
 local function finish(id,result,note)
  local t=trials[id]
  if not t or t.closed then diagnostics("INVALID_TRIAL",asstr(id));return end
  if result~="yes" and result~="no" and result~="unknown" then
   diagnostics("INVALID_RESULT",result);return
  end
  if result=="yes" and (not t.observed or t.observed=="") then
   diagnostics("MISSING_OBSERVATION","trial="..id);return
  end
  local match="unknown"
  if result=="yes" then match=(t.observed==t.expected) and "yes" or "no"
  elseif result=="no" then match="no" end
  local status=(result=="unknown" and "inconclusive")
   or ((result=="yes" and match=="yes") and "operator_observed" or "contradicted")
  append(prefix.."_validation.csv",
   "session,trial_id,press_frame,report_frame,phase,profile,source,control,expected_action,observed_action,result,match,status,notes",
   {session,id,t.frame,frame(),t.phase,profile.profile,t.source,t.control,t.expected,
    t.observed,result,match,status,note})
  t.closed=true
  annotate("TRIAL_CLOSED",id,status)
  pending_report()
 end
 local function command(line)
  local cmd,arg=line:match("^%s*([A-Z_]+)%s*:%s*(.-)%s*$")
  if cmd=="PHASE" and arg~="" then
   phase=arg;annotate("PHASE","",arg)
  elseif cmd=="OBSERVED" then
   local id,observed=arg:match("^(%d+):(.+)$")
   id=tonumber(id)
   if not id or not trials[id] or trials[id].closed then
    diagnostics("INVALID_TRIAL","OBSERVED:"..arg)
   else
    trials[id].observed=observed
    annotate("OBSERVED",id,observed)
    pending_report()
   end
  elseif cmd=="RESULT" then
   local id,result=arg:match("^(%d+):([a-z]+)$")
   if not id then diagnostics("INVALID_COMMAND",line)
   else finish(tonumber(id),result,"operator response") end
  elseif cmd=="NOTE" then annotate("NOTE","",arg)
  else diagnostics("INVALID_COMMAND",line) end
 end
 local function poll()
  for _=1,20 do
   local path=string.format("%s/%06d.cmd",queue,next_command)
   local f=io.open(path,"r")
   if not f then return end
   local s=f:read("*a");f:close()
   if s and s~="" then command(s:gsub("[\r\n]+$","")) end
   next_command=next_command+1
  end
 end
 local obj={}
 function obj:tick()
  local fr=frame()
  if fr==last_frame then return end
  last_frame=fr
  poll()
  local cur,source=inputs(port)
  if not cur then
   if old_source~="unavailable" then diagnostics("SOURCE_UNAVAILABLE",source) end
   old=nil;old_source="unavailable";return
  end
  if source~=old_source then diagnostics("SOURCE",source);old=nil;old_source=source end
  if old then
   local union={}
   for k in pairs(old) do union[k]=true end
   for k in pairs(cur) do union[k]=true end
   for _,key in ipairs(keys(union)) do
    local a,b=old[key],cur[key]
    if a~=b then
     local kind="CHANGE"
     if type(a)=="boolean" and type(b)=="boolean" then
      kind=b and "PRESS" or "RELEASE"
     elseif type(b)=="number" then kind="AXIS_CHANGE" end
     append(prefix.."_events.csv",
      "session,frame,phase,port,source,control,event,old_value,new_value,trial_id",
      {session,fr,phase,port,source,key,kind,asstr(a),asstr(b),
       (kind=="PRESS" and mapping[key]) and (trial_num+1) or ""})
     if kind=="PRESS" and mapping[key] then
      trial_num=trial_num+1
      trials[trial_num]={frame=fr,phase=phase,source=source,
       control=key,expected=mapping[key],observed="",closed=false}
      annotate("TRIAL_OPEN",trial_num,key.." => "..mapping[key])
      pending_report()
     end
    end
   end
  else
   local count=0;for _ in pairs(cur) do count=count+1 end
   diagnostics("BASELINE","controls="..count)
  end
  old=cur
 end
 function obj:run()
  -- The queue is session-specific: ignore commands from previous runs.
  local f=io.open(queue.."/session.txt","r")
  if f then
   local existing=f:read("*l");f:close()
   if existing then
    diagnostics("QUEUE_SESSION",existing)
   end
  end
  -- Sequential command filenames are consumed only once per run.
  while true do
   local f2=io.open(string.format("%s/%06d.cmd",queue,next_command),"r")
   if not f2 then break end
   f2:close();next_command=next_command+1
  end
  pending_report()
  diagnostics("START","source=canonical-default; independent_trials; queue_next="..next_command)
  annotate("START","","read-only")
  local advance=emu and (emu.frameadvance or emu.yield)
  if advance then while true do self:tick();advance() end
  elseif _G.event and _G.event.onframestart then
   _G.event.onframestart(function()self:tick()end,"goldeneye_manual_controls_v22")
  else diagnostics("FATAL","no frame callback") end
 end
 return obj
end
return M
