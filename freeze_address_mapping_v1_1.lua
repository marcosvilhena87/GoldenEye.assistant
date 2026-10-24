-- Freeze Address Mapping v1.1 -- automatic transition detection (read-only).
-- Use System Bus virtual alias candidates. No RAM writes, no cheat manipulation.
local DOMAIN="System Bus"
local ADDRS={{"kseg0_alias",0x8002C90C},{"kseg1_alias",0xA002C90C},{"physical_same",0x0002C90C}}
local STABLE=30
local MAX_FRAMES=36000
assert(memory and memory.getmemorydomainlist and memory.read_u8 and
       emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
local domain=false
for _,n in ipairs(memory.getmemorydomainlist()) do if n==DOMAIN then domain=true end end
assert(domain,"System Bus unavailable; refusing capture")
local function exists(p)
 local f=io.open(p,"rb");if f then f:close();return true end;return false
end
local function exclusive(p)
 assert(not exists(p),"Refusing overwrite "..p)
 return assert(io.open(p,"wb"))
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="freeze_address_v1_1_"..sid
local timeline=exclusive("output/csv/"..stem.."_timeline.csv")
local events=exclusive("output/csv/"..stem.."_events.csv")
local termination=exclusive("output/csv/"..stem.."_termination.csv")
timeline:write("session,frame,candidate,address_hex,read_ok,value_u8,state\n")
events:write("session,frame,event,from_state,to_state,run_start_frame,run_frames,kseg0_u8,kseg1_u8,details\n")
termination:write("session,frame,reason,frames,read_errors,alias_mismatches\n")
local pointer=assert(io.open("output/sessions/freeze_address_v1_1_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local prev,run_state,run_start,run_length,confirmed=nil,nil,nil,0,nil
local reason,reads_failed,mismatches="frame_limit",0,0
local last_frame=emu.framecount()
local function logevent(frame,kind,from,to,start,count,a,b,details)
 events:write(table.concat({sid,frame,kind,from or "",to or "",start or "",count or "",
   a or "",b or "",details or ""},","),"\n");events:flush()
 print("[freeze.address.v1.1] "..kind.." frame="..frame.." "..(from or "").." -> "..(to or ""))
end
print("[freeze.address.v1.1] session="..sid.." stable_frames="..STABLE)
print("[freeze.address.v1.1] Toggle Freeze manually OFF/ON/OFF/ON. STOP command: python tools/send_freeze_address_v1_1.py STOP")
for tick=1,MAX_FRAMES do
 local frame=emu.framecount()
 last_frame=frame
 if prev and frame~=prev+1 then reason="timeline_discontinuity";logevent(frame,"DISCONTINUITY","","",frame,0,"","","nonsequential_frame");break end
 prev=frame
 local raw={}
 for _,entry in ipairs(ADDRS) do
  local ok,v=pcall(memory.read_u8,entry[2],DOMAIN)
  if not ok or type(v)~="number" or v<0 or v>255 or v%1~=0 then
   reads_failed=reads_failed+1
   timeline:write(table.concat({sid,frame,entry[1],string.format("0x%08X",entry[2]),"0","","ERROR"},","),"\n")
   raw[entry[1]]=nil
  else
   local state=(v==0 and "OFF") or (v==255 and "ON") or "OTHER"
   raw[entry[1]]=v
   timeline:write(table.concat({sid,frame,entry[1],string.format("0x%08X",entry[2]),"1",v,state},","),"\n")
  end
 end
 local a,b=raw.kseg0_alias,raw.kseg1_alias
 local agree=(a~=nil and b~=nil and a==b and (a==0 or a==255))
 local state=agree and (a==0 and "OFF" or "ON") or "UNKNOWN"
 if not agree then
  mismatches=mismatches+1
  if run_state~="UNKNOWN" then logevent(frame,"ALIAS_UNCERTAIN",confirmed,"UNKNOWN",frame,1,a,b,"read_error_mismatch_or_nonbinary") end
 end
 if state~=run_state then run_state=state;run_start=frame;run_length=1
 else run_length=run_length+1 end
 if state~="UNKNOWN" and run_length==STABLE then
  if confirmed==nil then
   logevent(frame,"BASELINE_CONFIRMED","",state,run_start,run_length,a,b,"confirmed_after_consecutive_samples")
  elseif confirmed~=state then
   logevent(frame,"TRANSITION_CONFIRMED",confirmed,state,run_start,run_length,a,b,"effective_change_at_run_start")
  else
   logevent(frame,"STATE_RECONFIRMED",confirmed,state,run_start,run_length,a,b,"alias_uncertainty_recovered")
  end
  confirmed=state
 end
 if frame%60==0 then timeline:flush() end
 local stop=string.format("output/commands/%s_STOP.txt",stem)
 if exists(stop) then
  local f=assert(io.open(stop,"rb"));local s=f:read("*a");f:close()
  if s:gsub("%s+$","")=="STOP:"..sid then reason="stop";break end
  reason="invalid_stop_marker";break
 end
 emu.frameadvance()
end
timeline:close();events:close()
termination:write(table.concat({sid,last_frame,reason,(prev and last_frame or 0),reads_failed,mismatches},","),"\n")
termination:close()
print("[freeze.address.v1.1] finished session="..sid.." reason="..reason.." read_errors="..reads_failed.." mismatches="..mismatches)
