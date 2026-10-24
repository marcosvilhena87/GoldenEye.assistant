-- Spatial Target Alignment Discovery v1.7. Read-only full-RDRAM snapshots.
-- Configure these two values only after checking the BizHawk domain.
local DOMAIN=nil -- "RDRAM"
local EXPECTED_SIZE=nil -- 8388608
local ROOT="output/"
local CHUNK=4096
local MAX_FRAMES=36000
local LABELS={
 BOND_BASELINE=true,BOND_MOVE_LEFT=true,BOND_MOVE_RIGHT=true,
 BOND_MOVE_FORWARD=true,BOND_MOVE_BACK=true,BOND_ROTATE_LEFT=true,
 BOND_ROTATE_RIGHT=true,BOND_RETURN=true,
 SOLDIER_STATIONARY=true,SOLDIER_MOVED=true,
 ONE_GUARD_VISIBLE=true,NO_GUARD_VISIBLE=true,
 AUTOAIM_ON=true,AUTOAIM_OFF=true
}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"Missing BizHawk APIs")
if DOMAIN==nil or EXPECTED_SIZE==nil then print("[spatial.v1.7] Set verified DOMAIN and EXPECTED_SIZE");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Invalid/unverified domain")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local base="spatial_v1_7_"..sid
local function exclusive(path,header)
 local f=io.open(path,"rb");if f then f:close();error("Refusing overwrite: "..path) end
 f=assert(io.open(path,"wb"));if header then f:write(header,"\n") end;f:close()
end
local function append(path,row)
 local f=assert(io.open(path,"ab"));f:write(row,"\n");f:close()
end
local markers=ROOT.."csv/"..base.."_markers.csv"
local snapshots=ROOT.."csv/"..base.."_snapshots.csv"
local termination=ROOT.."csv/"..base.."_termination.csv"
local discontinuities=ROOT.."csv/"..base.."_discontinuities.csv"
exclusive(markers,"session,sample_index,frame,label")
exclusive(snapshots,"session,sample_index,frame,label,path,size_bytes")
exclusive(termination,"session,sample_index,frame,reason,pending_label,ticks")
exclusive(discontinuities,"session,sample_index,previous_frame,frame,delta")
local pointer=ROOT.."sessions/spatial_v1_7_session.txt"
local p=assert(io.open(pointer,"wb"));p:write(sid,"\n");p:close()
local next_command=1
local previous_frame=nil
local last_sample=0
local ticks=0
local reason="frame_limit"
local pending="NONE"
local function capture(label,tick,frame)
 local name=base.."_"..string.format("%04d",next_command).."_"..label..".bin"
 local path=ROOT.."archive/"..name
 exclusive(path,nil)
 local f=assert(io.open(path,"ab"))
 for start=0,EXPECTED_SIZE-1,CHUNK do
  local buf={}
  for i=0,math.min(CHUNK,EXPECTED_SIZE-start)-1 do
   local b=memory.read_u8(start+i,DOMAIN)
   assert(type(b)=="number" and b%1==0 and b>=0 and b<=255,"Invalid byte")
   buf[#buf+1]=string.char(b)
  end
  f:write(table.concat(buf))
 end
 f:close()
 append(snapshots,table.concat({sid,tick,frame,label,path,EXPECTED_SIZE},","))
 append(markers,table.concat({sid,tick,frame,label},","))
 print("[spatial.v1.7] captured "..label.." frame="..frame.." file="..name)
end
print("[spatial.v1.7] session="..sid.." read-only; snapshots are full 8 MiB; do NOT load savestates within session")
for tick=1,MAX_FRAMES do
 ticks=tick
 local frame=emu.framecount()
 if previous_frame~=nil and frame~=previous_frame+1 then
  append(discontinuities,table.concat({sid,tick,previous_frame,frame,frame-previous_frame},","))
  reason="timeline_discontinuity"
  break
 end
 previous_frame=frame
 last_sample=tick
 local command=ROOT.."commands/"..base.."_"..string.format("%04d",next_command)..".txt"
 local f=io.open(command,"rb")
 if f then
  local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  if label=="STOP" then
   append(markers,table.concat({sid,tick,frame,label},","))
   reason="stop"
   print("[spatial.v1.7] marked STOP frame="..frame)
   break
  elseif label and LABELS[label] then
   pending=label
   capture(label,tick,frame)
   pending="NONE"
   next_command=next_command+1
  else reason="invalid_marker";break end
 end
 emu.frameadvance()
end
append(termination,table.concat({sid,last_sample,emu.framecount(),reason,pending,ticks},","))
print("[spatial.v1.7] FINISHED session="..sid.." reason="..reason)
