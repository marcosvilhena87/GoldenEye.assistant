-- v1.8 full KSEG0 candidate snapshot, READ ONLY. Capture P1 P2 P3 and camera.
local BUS="System Bus";local BASE=0x80000000;local SIZE=0x800000
local F0=0x8002C90C;local F1=0xA002C90C
local STABLE=30;local HOLD=120;local LIMIT=90000
assert(memory and memory.read_u8 and memory.getmemorydomainlist and emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
local found=false
for _,x in ipairs(memory.getmemorydomainlist()) do if x==BUS then found=true end end
assert(found,"System Bus domain missing")
local function exists(p) local f=io.open(p,"rb");if f then f:close();return true end return false end
local function exclusive(path) assert(not exists(path),"Refusing overwrite "..path);return assert(io.open(path,"wb")) end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="enemy_freeze_v1_8_"..sid
local manifest=exclusive("output/csv/"..stem.."_manifest.csv")
manifest:write("session,frame,after_frame,epoch,phase,state,start_hex,bytes,file,notes\n");manifest:flush()
local events=exclusive("output/csv/"..stem.."_events.csv")
events:write("session,frame,event,state,on_epoch,run_frames\n");events:flush()
local pointer=assert(io.open("output/sessions/enemy_freeze_v1_8_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local state,run,epoch,prev=nil,0,0,nil
local stop_reason="frame_limit";local captured=0;local unknown=0;local cam_done=false
local function event(frame,name)
 events:write(table.concat({sid,frame,name,state or "",epoch,run},","),"\n");events:flush()
 print("[enemy.freeze.v1.8] "..name.." frame="..frame.." epoch="..epoch)
end
local function snapshot(frame,phase)
 local path=string.format("output/raw/%s_e%02d_%s.bin",stem,epoch,phase)
 local f=exclusive(path);local chunk={}
 for offset=0,SIZE-1 do
  local ok,v=pcall(memory.read_u8,BASE+offset,BUS)
  if not ok or type(v)~="number" or v%1~=0 or v<0 or v>255 then
   f:close();error("Incomplete snapshot; invalid at "..offset.." "..path)
  end
  chunk[#chunk+1]=string.char(v)
  if #chunk==4096 then f:write(table.concat(chunk));chunk={} end
 end
 if #chunk>0 then f:write(table.concat(chunk)) end
 f:close()
 local after=emu.framecount()
 local note=after==frame and "same_frame_kseg0_unvalidated" or "frame_changed_invalid"
 manifest:write(table.concat({sid,frame,after,epoch,phase,state,"0x000000",SIZE,path,note},","),"\n");manifest:flush()
 captured=captured+1;event(frame,"CAPTURE_"..phase)
end
print("[enemy.freeze.v1.8] session="..sid.." ON P1, OFF motion, ON P2, OFF motion, ON P3, CAM, STOP")
print("[enemy.freeze.v1.8] Capture ON stable @30, hold @120; wait for CAPTURE_hold each time.")
for i=1,LIMIT do
 local frame=emu.framecount()
 if prev and frame~=prev+1 then stop_reason="timeline_discontinuity";break end
 prev=frame
 local aok,a=pcall(memory.read_u8,F0,BUS)
 local bok,b=pcall(memory.read_u8,F1,BUS)
 local current="UNKNOWN"
 if aok and bok and a==b and a==0 then current="OFF"
 elseif aok and bok and a==b and a==255 then current="ON" end
 if current=="UNKNOWN" then unknown=unknown+1 end
 if current~=state then
  state=current;run=1
  if current=="ON" then epoch=epoch+1 end
  event(frame,"STATE_CHANGE")
 else run=run+1 end
 if state=="ON" and epoch<=3 then
  if run==STABLE then snapshot(frame,"stable") end
  if run==HOLD then snapshot(frame,"hold") end
 end
 local cam="output/commands/"..stem.."_CAM.txt"
 if exists(cam) and not cam_done then
  local f=assert(io.open(cam,"rb"));local v=f:read("*a");f:close()
  if v:gsub("%s+$","")~="CAM:"..sid then stop_reason="invalid_cam";break end
  if state~="ON" or epoch~=3 or run<HOLD then stop_reason="cam_wrong_state";break end
  snapshot(frame,"camera");cam_done=true
 end
 local stop="output/commands/"..stem.."_STOP.txt"
 if exists(stop) then
  local f=assert(io.open(stop,"rb"));local v=f:read("*a");f:close()
  stop_reason=v:gsub("%s+$","")=="STOP:"..sid and "stop" or "invalid_stop"
  break
 end
 emu.frameadvance()
end
manifest:close();events:close()
local t=exclusive("output/csv/"..stem.."_termination.csv")
t:write("session,frame,reason,on_epochs,captures,unknown_frames,camera_captured\n")
t:write(table.concat({sid,prev or 0,stop_reason,epoch,captured,unknown,cam_done and 1 or 0},","),"\n");t:close()
print("[enemy.freeze.v1.8] FINISHED reason="..stop_reason.." session="..sid)
