-- v1.6 Controlled Movement & Temporal Validation: read-only KSEG0 windows.
-- Operator toggles Freeze manually. CAM command requests a camera-only snapshot.
local BUS="System Bus";local BASE=0x80000000
local REGIONS={{0x0D5000,0x3500},{0x0E6800,0x3500},{0x0D3800,0x900}}
local FLAGS={0x8002C90C,0xA002C90C}
local STABLE=30;local HOLD=120;local LIMIT=90000
assert(memory and memory.getmemorydomainlist and emu and emu.framecount and emu.frameadvance,"API unavailable")
local domain=false
for _,v in ipairs(memory.getmemorydomainlist()) do if v==BUS then domain=true end end
assert(domain,"System Bus missing")
local function exists(p) local f=io.open(p,"rb");if f then f:close();return true end;return false end
local function fresh(p) assert(not exists(p),"Refuse overwrite: "..p);return assert(io.open(p,"wb")) end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local stem="enemy_freeze_v1_6_"..sid
local csv=fresh("output/csv/"..stem.."_manifest.csv")
csv:write("session,frame,after_frame,epoch,phase,region,start_hex,bytes,file,state,notes\n");csv:flush()
local events=fresh("output/csv/"..stem.."_events.csv")
events:write("session,frame,event,epoch,state,run_frames\n");events:flush()
local term=fresh("output/csv/"..stem.."_termination.csv")
term:write("session,frame,reason,on_epochs,captures,uncertain_frames\n");term:flush()
local pointer=assert(io.open("output/sessions/enemy_freeze_v1_6_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local frame_prev=nil;local state=nil;local run=0;local epoch=0;local on_epochs=0
local captures=0;local unknown=0;local reason="frame_limit"
local camera_done={}
local function log(frame,ev)
 events:write(table.concat({sid,frame,ev,epoch,state or "",run},","),"\n");events:flush()
 print("[enemy.freeze.v1.6] "..ev.." epoch="..epoch.." frame="..frame)
end
local function capture(frame,phase)
 for i,region in ipairs(REGIONS) do
  local start,len=region[1],region[2]
  local path=string.format("output/raw/%s_e%02d_%s_r%d.bin",stem,epoch,phase,i)
  local out=fresh(path)
  local chunk={}
  for j=0,len-1 do
   local ok,v=pcall(memory.read_u8,BASE+start+j,BUS)
   if not ok or type(v)~="number" or v<0 or v>255 or v%1~=0 then
    out:close();error("Unmapped read; incomplete file: "..path)
   end
   chunk[#chunk+1]=string.char(v)
   if #chunk==4096 then out:write(table.concat(chunk));chunk={} end
  end
  if #chunk>0 then out:write(table.concat(chunk)) end
  out:close()
  local after=emu.framecount()
  local notes=after==frame and "same_frame_kseg0_candidate" or "frame_changed_invalid"
  csv:write(table.concat({sid,frame,after,epoch,phase,i,string.format("0x%06X",start),
     len,path,state or "",notes},","),"\n");csv:flush()
  captures=captures+1
 end
 log(frame,"CAPTURE_"..phase)
end
print("[enemy.freeze.v1.6] session="..sid.." ON1 OFF ON2 OFF ON3; maintain ON >=150f.")
print("[enemy.freeze.v1.6] After ON3, turn camera without moving Bond, send CAM; then STOP.")
print("[enemy.freeze.v1.6] python tools/send_enemy_freeze_v1_6.py CAM or STOP")
for t=1,LIMIT do
 local f=emu.framecount()
 if frame_prev and f~=frame_prev+1 then reason="discontinuity";break end
 frame_prev=f
 local ok1,a=pcall(memory.read_u8,FLAGS[1],BUS)
 local ok2,b=pcall(memory.read_u8,FLAGS[2],BUS)
 local now="UNKNOWN"
 if ok1 and ok2 and a==b and a==0 then now="OFF"
 elseif ok1 and ok2 and a==b and a==255 then now="ON" end
 if now=="UNKNOWN" then unknown=unknown+1 end
 if now~=state then
  state=now;run=1
  if now=="ON" then epoch=epoch+1;on_epochs=on_epochs+1 end
  log(f,"STATE_CHANGE")
 else run=run+1 end
 if state=="ON" and on_epochs<=3 then
  if run==STABLE then capture(f,"stable") end
  if run==HOLD then capture(f,"hold") end
 end
 local cam="output/commands/"..stem.."_CAM.txt"
 if exists(cam) and not camera_done[cam] then
  local h=assert(io.open(cam,"rb"));local val=h:read("*a");h:close()
  if val:gsub("%s+$","")~="CAM:"..sid then reason="bad_cam_command";break end
  if state=="ON" and run>=HOLD and on_epochs==3 then
   capture(f,"camera");camera_done[cam]=true
  else reason="cam_outside_on3_hold";break end
 end
 local stop="output/commands/"..stem.."_STOP.txt"
 if exists(stop) then
  local h=assert(io.open(stop,"rb"));local val=h:read("*a");h:close()
  reason=(val:gsub("%s+$","")=="STOP:"..sid) and "stop" or "bad_stop"
  break
 end
 emu.frameadvance()
end
term:write(table.concat({sid,frame_prev or 0,reason,on_epochs,captures,unknown},","),"\n")
csv:close();events:close();term:close()
print("[enemy.freeze.v1.6] FINISHED "..reason.." session="..sid)
