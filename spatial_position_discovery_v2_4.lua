-- Spatial v2.4 controlled movement. Read only: verify RDRAM domain first.
local DOMAIN=nil -- set "RDRAM" after verification
local EXPECTED_SIZE=nil -- set 8388608 after verification
local ROOT="output/"
local LIMIT=24000
local START,LAST=0x3B30B0,0x3B30FF
local ORDER={"P0_HOLD","FORWARD","P1_HOLD","BACK","P0_RETURN_HOLD","ROTATE","P0_ROTATED_HOLD","FORWARD_AGAIN","P2_HOLD","STOP"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"BizHawk API missing")
if not DOMAIN or not EXPECTED_SIZE then print("[spatial.v2.4] Set verified DOMAIN and EXPECTED_SIZE");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"RDRAM mismatch")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="spatial_v2_4_"..sid
local function exclusive(name,header)
 local old=io.open(name,"rb");if old then old:close();error("Refusing overwrite "..name)end
 local f=assert(io.open(name,"wb"));f:write(header,"\n");return f
end
local sample=exclusive(ROOT.."csv/"..stem.."_window.csv","session,frame,phase,offset,byte_hex")
local markers=exclusive(ROOT.."csv/"..stem.."_markers.csv","session,frame,label")
local term=exclusive(ROOT.."csv/"..stem.."_termination.csv","session,frame,reason")
local discontinuities=exclusive(ROOT.."csv/"..stem.."_discontinuities.csv","session,previous_frame,frame,delta")
local pointer=assert(io.open(ROOT.."sessions/spatial_v2_4_session.txt","wb"));pointer:write(sid,"\n");pointer:close()
local function write(file,s)file:write(s,"\n");file:flush()end
local nextcmd=1;local phase="PRESTART";local prev=nil;local frame=emu.framecount();local reason="frame_limit"
print("[spatial.v2.4] session="..sid.." read-only; no savestates")
for i=1,LIMIT do
 frame=emu.framecount()
 if prev and frame~=prev+1 then
  write(discontinuities,table.concat({sid,prev,frame,frame-prev},","))
  reason="timeline_discontinuity";break
 end
 prev=frame
 local name=ROOT.."commands/"..stem.."_"..string.format("%04d",nextcmd)..".txt"
 local file=io.open(name,"rb")
 if file then
  local command=file:read("*a");file:close()
  local label=command:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  if label~=ORDER[nextcmd] then reason="invalid_marker";break end
  phase=label;write(markers,table.concat({sid,frame,label},","))
  print("[spatial.v2.4] marked "..label.." frame="..frame)
  nextcmd=nextcmd+1
  if label=="STOP" then reason="stop";break end
 end
 for offset=START,LAST do
  local b=memory.read_u8(offset,DOMAIN)
  assert(type(b)=="number" and b>=0 and b<256 and b%1==0,"Bad RDRAM read")
  write(sample,table.concat({sid,frame,phase,string.format("0x%06X",offset),string.format("%02X",b)},","))
 end
 emu.frameadvance()
end
write(term,table.concat({sid,frame,reason},","))
sample:close();markers:close();term:close();discontinuities:close()
print("[spatial.v2.4] FINISHED session="..sid.." reason="..reason)
