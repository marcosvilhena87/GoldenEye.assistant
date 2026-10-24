-- Enemy Coordinate Discovery v1: Freeze-synchronized RAW System Bus snapshots.
-- Read-only; all addresses are hypotheses, not verified XYZ locations.
local BUS="System Bus"
local BASE=0x80000000   -- KSEG0 hypothesis; not the physical offset domain.
local SIZE=0x800000     -- 8 MiB, verify game/core before interpreting dumps.
local FLAG0,FLAG1=0x8002C90C,0xA002C90C
local STABLE=30
local HOLD=120
local MAX_FRAMES=90000
local CHUNK=4096
assert(memory and memory.getmemorydomainlist and memory.read_u8 and
       emu and emu.framecount and emu.frameadvance,"Missing BizHawk API")
local has=false
for _,d in ipairs(memory.getmemorydomainlist()) do if d==BUS then has=true end end
assert(has,"System Bus unavailable")
local function exists(p) local f=io.open(p,"rb");if f then f:close();return true end;return false end
local function fresh(p) assert(not exists(p),"Refusing overwrite "..p);return assert(io.open(p,"wb")) end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="enemy_freeze_v1_"..sid
local manifest=fresh("output/csv/"..stem.."_manifest.csv")
manifest:write("session,frame,frame_after,epoch,phase,state,start_offset,bytes,file,notes\n");manifest:flush()
local events=fresh("output/csv/"..stem.."_events.csv")
events:write("session,frame,event,state,run_start,run_frames,epoch\n");events:flush()
local term=fresh("output/csv/"..stem.."_termination.csv")
term:write("session,frame,reason,captures,epochs,unknown_frames\n");term:flush()
local pointer=assert(io.open("output/sessions/enemy_freeze_v1_session.txt","wb"));pointer:write(sid,"\n");pointer:close()
local state,run_start,run_len,epoch,prev=nil,nil,0,0,nil
local snapshots,unknown,reason=0,0,"frame_limit"
local captured={}
local function log(frame,kind,status,start,count)
 events:write(table.concat({sid,frame,kind,status or "",start or "",count or "",epoch},","),"\n");events:flush()
 print("[enemy.freeze.v1] "..kind.." frame="..frame.." state="..tostring(status).." epoch="..epoch)
end
local function dump(frame,phase,status)
 local name=stem.."_"..string.format("%02d",epoch).."_"..phase..".bin"
 local path="output/raw/"..name
 local out=fresh(path)
 local bytes={}
 for offset=0,SIZE-1 do
  local ok,v=pcall(memory.read_u8,BASE+offset,BUS)
  if not ok or type(v)~="number" or v%1~=0 or v<0 or v>255 then
   out:close()
   error("Bus read failed at offset "..string.format("0x%X",offset)..
         "; incomplete snapshot preserved, do not analyze: "..path)
  end
  bytes[#bytes+1]=string.char(v)
  if #bytes==CHUNK then out:write(table.concat(bytes));bytes={} end
 end
 if #bytes>0 then out:write(table.concat(bytes)) end
 out:close()
 local after=emu.framecount()
 local notes=(after==frame) and "raw_bus_kseg0_unvalidated" or "frame_changed_during_dump"
 manifest:write(table.concat({sid,frame,after,epoch,phase,status,"0x000000",SIZE,path,notes},","),"\n")
 manifest:flush();snapshots=snapshots+1
 print("[enemy.freeze.v1] captured "..phase.." "..path.." frame="..frame.." "..notes)
end
print("[enemy.freeze.v1] session="..sid.."; verify RAM Watch; OFF/ON/OFF/ON/OFF/ON, stay >=150 frames each")
print("[enemy.freeze.v1] STOP: python tools/send_enemy_freeze_v1.py STOP")
for tick=1,MAX_FRAMES do
 local frame=emu.framecount()
 if prev and frame~=prev+1 then reason="timeline_discontinuity";break end
 prev=frame
 local ok0,a=pcall(memory.read_u8,FLAG0,BUS)
 local ok1,b=pcall(memory.read_u8,FLAG1,BUS)
 local observed=(ok0 and ok1 and a==b and (a==0 or a==255))
     and (a==0 and "OFF" or "ON") or "UNKNOWN"
 if observed=="UNKNOWN" then unknown=unknown+1 end
 if observed~=state then
  state=observed;run_start=frame;run_len=1
  if observed~="UNKNOWN" then epoch=epoch+1;log(frame,"RUN_START",observed,run_start,run_len) end
 else run_len=run_len+1 end
 if observed~="UNKNOWN" then
  if run_len==STABLE then
   log(frame,"STABLE",observed,run_start,run_len)
   if observed=="ON" then dump(frame,"on_stable",observed)
   else dump(frame,"off_stable",observed) end
  elseif run_len==HOLD and observed=="ON" then
   dump(frame,"on_hold",observed)
  end
 end
 if frame%120==0 then events:flush() end
 local stop="output/commands/"..stem.."_STOP.txt"
 if exists(stop) then
  local f=assert(io.open(stop,"rb"));local marker=f:read("*a");f:close()
  if marker:gsub("%s+$","")=="STOP:"..sid then reason="stop" else reason="invalid_stop" end
  break
 end
 emu.frameadvance()
end
local last=prev or emu.framecount()
term:write(table.concat({sid,last,reason,snapshots,epoch,unknown},","),"\n")
manifest:close();events:close();term:close()
print("[enemy.freeze.v1] FINISHED reason="..reason.." snapshots="..snapshots.." session="..sid)
