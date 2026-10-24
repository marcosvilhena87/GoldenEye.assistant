-- Candidate probe 0D36F4 / 0D3720. Read-only, 1-byte offsets from Cheat Search.
local DOMAIN=nil -- VERIFY THEN SET "RDRAM"
local EXPECTED_SIZE=nil -- VERIFY THEN SET 8388608
local ROOT="output/"
local MAX_FRAMES=36000
local OFFSETS={{0x0D36F4,"0x0D36F4"},{0x0D3720,"0x0D3720"}}
local LABELS={BASELINE=true,FORWARD=true,STOP_MOVE=true,ROTATE=true,STOP_ROTATE=true,
 BACK=true,NO_TARGET=true,TARGET_VISIBLE=true,AUTOAIM_ON=true,AUTOAIM_OFF=true,
 WEAPON_CHANGE=true,STOP=true}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and
 emu.framecount and emu.frameadvance,"Missing BizHawk APIs")
if not DOMAIN or not EXPECTED_SIZE then
 print("[probe.0d36] Configure verified DOMAIN/EXPECTED_SIZE; stopped");return
end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and
 memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"RDRAM mismatch")
for _,o in ipairs(OFFSETS) do assert(o[1]<EXPECTED_SIZE,"Offset out of range") end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="probe_0d36_0d37_"..sid
local function create(filename,header)
 local f=io.open(filename,"rb")
 if f then f:close();error("Refusing overwrite "..filename) end
 local out=assert(io.open(filename,"wb"));out:write(header,"\n");out:flush()
 return out
end
local timeline=create(ROOT.."csv/"..stem.."_timeline.csv",
 "session,frame,phase,offset_hex,byte_hex,u8,changed")
local markers=create(ROOT.."csv/"..stem.."_markers.csv","session,frame,label")
local termination=create(ROOT.."csv/"..stem.."_termination.csv","session,frame,reason")
local discontinuities=create(ROOT.."csv/"..stem.."_discontinuities.csv",
 "session,previous_frame,frame,delta")
local pointer=assert(io.open(ROOT.."sessions/probe_0d36_0d37_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local function record(fp,line)fp:write(line,"\n");fp:flush()end
local command_index,phase,previous_frame=1,"PRESTART",nil
local last_byte={}
local reason="frame_limit"
local frame=emu.framecount()
print("[probe.0d36] session="..sid.." read-only; wait for marked before action")
for tick=1,MAX_FRAMES do
 frame=emu.framecount()
 if previous_frame and frame~=previous_frame+1 then
  record(discontinuities,table.concat({sid,previous_frame,frame,
                                       frame-previous_frame},","))
  reason="timeline_discontinuity";break
 end
 previous_frame=frame
 local path=ROOT.."commands/"..stem.."_"..string.format("%04d",command_index)..".txt"
 local fp=io.open(path,"rb")
 if fp then
  local body=fp:read("*a");fp:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  if not label or not LABELS[label] then reason="invalid_marker";break end
  phase=label;record(markers,table.concat({sid,frame,label},","))
  print("[probe.0d36] marked "..label.." frame="..frame)
  command_index=command_index+1
  if label=="STOP" then reason="stop";break end
 end
 for _,entry in ipairs(OFFSETS) do
  local address,hex=entry[1],entry[2]
  local val=memory.read_u8(address,DOMAIN)
  assert(type(val)=="number" and val>=0 and val<256 and val%1==0,
         "Invalid read at "..hex)
  local changed=(last_byte[hex]~=nil and last_byte[hex]~=val) and 1 or 0
  record(timeline,table.concat({sid,frame,phase,hex,
      string.format("%02X",val),val,changed},","))
  last_byte[hex]=val
 end
 emu.frameadvance()
end
record(termination,table.concat({sid,frame,reason},","))
timeline:close();markers:close();termination:close();discontinuities:close()
print("[probe.0d36] FINISHED session="..sid.." reason="..reason)
