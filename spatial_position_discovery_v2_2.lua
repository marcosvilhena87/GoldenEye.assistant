-- v2.2 neighboring-memory probe; read-only, explicit verification required.
-- NEW experiment; no v1.9 file is overwritten.
local DOMAIN=nil -- "RDRAM" after verification
local EXPECTED_SIZE=nil -- 8388608 after verification
local ROOT="output/"
local MAX_FRAMES=18000
local START=0x3B30B0
local LAST=0x3B30FF
local STEP=1
local ORDER={"STILL","MOVE","HOLD","ROTATE","ROTATE_HOLD","STOP"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"BizHawk APIs missing")
if DOMAIN==nil or EXPECTED_SIZE==nil then print("[spatial.v2.2] Configure verified memory domain and size");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Invalid memory domain")
assert(START>=0 and LAST<EXPECTED_SIZE and START<=LAST and STEP>=1,"Invalid window")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="spatial_v2_2_"..sid
local function create(path,header)
 local f=io.open(path,"rb");if f then f:close();error("Refusing overwrite "..path) end
 f=assert(io.open(path,"wb"));f:write(header,"\n");return f
end
local function append(f,line)f:write(line,"\n");f:flush()end
local samples=create(ROOT.."csv/"..stem.."_window.csv","session,frame,phase,offset,byte_hex")
local markers=create(ROOT.."csv/"..stem.."_markers.csv","session,frame,label")
local terminal=create(ROOT.."csv/"..stem.."_termination.csv","session,frame,reason")
local jumps=create(ROOT.."csv/"..stem.."_discontinuities.csv","session,previous_frame,frame,delta")
local ptr=assert(io.open(ROOT.."sessions/spatial_v2_2_session.txt","wb"));ptr:write(sid,"\n");ptr:close()
local phase="PRESTART";local nextcmd=1;local prev=nil;local reason="frame_limit";local frame=emu.framecount()
print("[spatial.v2.2] session="..sid.." read-only window 0x3B30B0..0x3B30FF; no savestates")
for i=1,MAX_FRAMES do
 frame=emu.framecount()
 if prev and frame~=prev+1 then
  append(jumps,table.concat({sid,prev,frame,frame-prev},","))
  reason="timeline_discontinuity";break
 end
 prev=frame
 local command=ROOT.."commands/"..stem.."_"..string.format("%04d",nextcmd)..".txt"
 local f=io.open(command,"rb")
 if f then
  local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z_]+)\n$")
  if label~=ORDER[nextcmd] then reason="invalid_marker";break end
  phase=label;append(markers,table.concat({sid,frame,label},","))
  print("[spatial.v2.2] marked "..label.." frame="..frame)
  nextcmd=nextcmd+1
  if label=="STOP" then reason="stop";break end
 end
 for addr=START,LAST,STEP do
  local value=memory.read_u8(addr,DOMAIN)
  assert(type(value)=="number" and value>=0 and value<=255 and value%1==0,"Invalid byte")
  append(samples,table.concat({sid,frame,phase,string.format("0x%06X",addr),string.format("%02X",value)},","))
 end
 emu.frameadvance()
end
append(terminal,table.concat({sid,frame,reason},","))
samples:close();markers:close();terminal:close();jumps:close()
print("[spatial.v2.2] FINISHED session="..sid.." reason="..reason)
