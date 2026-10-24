-- Spatial Position Discovery v1.9 - independent, read-only candidate validation.
-- Set DOMAIN/EXPECTED_SIZE only after verification in BizHawk memory domains.
local DOMAIN=nil -- "RDRAM"
local EXPECTED_SIZE=nil -- 8388608
local ROOT="output/"
local LIMIT=54000
local ADDR={0x3B30D8,0x3B30D0} -- v1.8 hypotheses, NOT validated positions
local ORDER={"BASELINE_HOLD","FORWARD","FORWARD_HOLD","BACK","BACK_HOLD","ROTATE","ROTATE_HOLD","STRAFE","STRAFE_HOLD","STOP"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount,"Missing BizHawk APIs")
if DOMAIN==nil or EXPECTED_SIZE==nil then print("[spatial.v1.9] Set verified DOMAIN and EXPECTED_SIZE");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Invalid RDRAM domain")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="spatial_v1_9_"..sid
local function exclusive(path,header)
 local old=io.open(path,"rb");if old then old:close();error("Refusing overwrite: "..path) end
 local f=assert(io.open(path,"wb"));if header then f:write(header,"\n") end;return f
end
local function append(f,row)f:write(row,"\n");f:flush()end
local rows=exclusive(ROOT.."csv/"..stem.."_samples.csv","session,frame,tick,phase,address,raw_be,be_float32")
local marks=exclusive(ROOT.."csv/"..stem.."_markers.csv","session,frame,tick,label")
local term=exclusive(ROOT.."csv/"..stem.."_termination.csv","session,frame,tick,reason,next_label")
local jumps=exclusive(ROOT.."csv/"..stem.."_discontinuities.csv","session,previous_frame,frame,delta")
local p=assert(io.open(ROOT.."sessions/spatial_v1_9_session.txt","wb"));p:write(sid,"\n");p:close()
local function sample(addr)
 local a,b,c,d=memory.read_u8(addr,DOMAIN),memory.read_u8(addr+1,DOMAIN),memory.read_u8(addr+2,DOMAIN),memory.read_u8(addr+3,DOMAIN)
 assert(a and b and c and d and a>=0 and a<256 and b>=0 and b<256 and c>=0 and c<256 and d>=0 and d<256,"Invalid RDRAM read")
 local n=((a*256+b)*256+c)*256+d
 local sign=a>=128 and -1 or 1
 local exponent=math.floor(n/8388608)%256
 local mantissa=n%8388608
 local value
 if exponent==255 then value="nonfinite"
 elseif exponent==0 then value=sign*(mantissa/8388608)*2^-126
 else value=sign*(1+mantissa/8388608)*2^(exponent-127) end
 return string.format("%08X",n),tostring(value)
end
local nextcmd=1
local phase="PRESTART"
local prev=nil
local reason="frame_limit"
local lastframe=emu.framecount()
local tick=0
print("[spatial.v1.9] session="..sid.." read-only; no savestates; candidate offsets unverified")
for i=1,LIMIT do
 tick=i
 local frame=emu.framecount();lastframe=frame
 if prev and frame~=prev+1 then
  append(jumps,table.concat({sid,prev,frame,frame-prev},","))
  reason="timeline_discontinuity";break
 end
 prev=frame
 local path=ROOT.."commands/"..stem.."_"..string.format("%04d",nextcmd)..".txt"
 local f=io.open(path,"rb")
 if f then
  local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z_]+)\n$")
  if label~=ORDER[nextcmd] then reason="invalid_marker";break end
  phase=label
  append(marks,table.concat({sid,frame,i,label},","))
  print("[spatial.v1.9] marked "..label.." frame="..frame)
  nextcmd=nextcmd+1
  if label=="STOP" then reason="stop";break end
 end
 for _,addr in ipairs(ADDR) do
  local raw,v=sample(addr)
  append(rows,table.concat({sid,frame,i,phase,string.format("0x%06X",addr),raw,v},","))
 end
 emu.frameadvance()
end
append(term,table.concat({sid,lastframe,tick,reason,ORDER[nextcmd] or "NONE"},","))
rows:close();marks:close();term:close();jumps:close()
print("[spatial.v1.9] FINISHED session="..sid.." reason="..reason)
