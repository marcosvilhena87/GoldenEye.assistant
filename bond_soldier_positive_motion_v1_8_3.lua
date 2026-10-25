-- Bond-Soldier Coordinate Correlation v1.8.3 (BizHawk NLua, READ ONLY)
-- ALL addresses are experimental; System Bus aliases of physical RDRAM.
local BUS="System Bus"
local FIELDS={{"bond_e8",0x0D33E8},{"bond_ec",0x0D33EC},{"bond_f0",0x0D33F0},{"bond_f4",0x0D33F4},{"soldier_1_a",0x20F594},{"soldier_1_b",0x20F5AC}}
local LABELS={BASELINE=true,FREEZE_ON=true,FREEZE_OFF=true,CAMERA_ONLY=true,BOND_MOVE=true,SOLDIER_MOVE=true,WRITE_PRE=true,WRITE_APPLIED=true,WRITE_OBSERVE=true,SOLDIER_STILL=true,SOLDIER_MOVING=true,SOLDIER_REFROZEN=true,STOP=true}
assert(memory and memory.getmemorydomainlist and memory.read_u8,"memory unavailable")
assert(emu and emu.framecount and emu.frameadvance,"frame API unavailable")
local exists=false
for _,v in ipairs(memory.getmemorydomainlist()) do if v==BUS then exists=true end end
assert(exists,"System Bus required")
local function rd(addr)
 local t={}
 for i=0,3 do
  local ok,n=pcall(memory.read_u8,addr+i,BUS)
  assert(ok and type(n)=="number" and n>=0 and n<=255 and n%1==0,"invalid byte read")
  t[i+1]=n
 end
 local raw=string.format("%02X%02X%02X%02X",t[1],t[2],t[3],t[4])
 local exp=(t[1]%128)*2+math.floor(t[2]/128)
 local mant=(t[2]%128)*65536+t[3]*256+t[4]
 local sign=t[1]>=128 and -1 or 1
 local f=nil
 if exp==0 then f=sign*(mant/8388608)*2^-126
 elseif exp<255 then f=sign*(1+mant/8388608)*2^(exp-127) end
 return raw,f
end
local function create(path,header)
 local old=io.open(path,"rb");assert(not old,"File already exists: "..path)
 local fp=assert(io.open(path,"wb"),"create output/csv first")
 fp:write(header,"\n");fp:flush();return fp
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local stem="bond_soldier_v1_8_3_"..sid
local csv=create("output/csv/"..stem.."_timeline.csv","session,frame,phase,field,offset_hex,kseg0_hex,kseg1_hex,float32_be,alias_equal,changed")
local marks=create("output/csv/"..stem.."_markers.csv","session,frame,label")
local term=create("output/csv/"..stem.."_termination.csv","session,frame,reason")
local f=assert(io.open("output/sessions/bond_soldier_v1_8_3_session.txt","wb"));f:write(sid,"\n");f:close()
local seq,phase,prev,previous_frame=1,"PRESTART",{},nil
local reason="frame_limit";local frame=emu.framecount()
print("[bond-soldier.v1.8.3] session="..sid.." READ ONLY. Command files: output/commands/"..stem.."_NNNN.txt; line: LABEL:<LABEL>")
for tick=1,36000 do
 frame=emu.framecount()
 if previous_frame and frame~=previous_frame+1 then reason="timeline_discontinuity";break end
 previous_frame=frame
 local path=string.format("output/commands/%s_%04d.txt",stem,seq)
 local cmd=io.open(path,"rb")
 if cmd then
  local body=cmd:read("*a");cmd:close()
  local label=body:gsub("^\239\187\191",""):gsub("\r\n","\n"):gsub("\r","\n"):match("^LABEL:([A-Z_0-9]+)\n?$")
  if not LABELS[label] then reason="invalid_marker";print("[bond-soldier.v1.8.3] INVALID "..path);break end
  phase=label;marks:write(string.format("%s,%d,%s\n",sid,frame,label));marks:flush()
  print("[bond-soldier.v1.8.3] MARKED "..label.." frame="..frame)
  seq=seq+1
  if label=="STOP" then reason="stop";break end
 end
 for _,item in ipairs(FIELDS) do
  local name,off=item[1],item[2]
  local a,v=rd(0x80000000+off)
  local b=rd(0xA0000000+off)
  local changed=prev[name] and prev[name]~=a and 1 or 0
  csv:write(string.format("%s,%d,%s,%s,0x%06X,%s,%s,%s,%d,%d\n",sid,frame,phase,name,off,a,b,v and string.format("%.9g",v) or "",a==b and 1 or 0,changed or 0))
  prev[name]=a
 end
 if tick%30==0 then csv:flush() end
 emu.frameadvance()
end
term:write(string.format("%s,%d,%s\n",sid,frame,reason))
csv:close();marks:close();term:close()
print("[bond-soldier.v1.8.3] DONE "..reason.." session="..sid)
