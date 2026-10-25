-- Bond Position Discovery v1.1 (READ ONLY); BizHawk NLua
local BUS="System Bus"
local BASES={0x0D33E8,0x0D33EC,0x0D33F0,0x0D33F4}
local MAX_FRAMES=54000
local allowed={BASELINE=true,FORWARD=true,HOLD_F=true,BACK=true,HOLD_B=true,STRAFE_LEFT=true,STRAFE_RIGHT=true,ROTATE=true,HOLD_ROT=true,WRITE_BEFORE=true,WRITE_AFTER=true,WRITE_HOLD1=true,WRITE_HOLD30=true,WRITE_HOLD120=true,RESTORE=true,STOP=true}
local function callable(t,k)
 if not t then return false end
 local ok,v=pcall(function() return t[k] end)
 return ok and v~=nil and (type(v)=="function" or type(v)=="userdata")
end
assert(callable(memory,"getmemorydomainlist") and callable(memory,"read_u8"),"BizHawk memory API missing")
assert(callable(emu,"frameadvance") and callable(emu,"framecount"),"BizHawk frame API missing")
local found=false
for _,d in ipairs(memory.getmemorydomainlist()) do if d==BUS then found=true end end
assert(found,"System Bus not available")
local function read(addr)
 local ok,v=pcall(memory.read_u8,addr,BUS)
 assert(ok and type(v)=="number" and v>=0 and v<256 and v%1==0,"Bad System Bus read at "..string.format("%08X",addr))
 return v
end
local function raw(base)
 local t={}
 for i=0,3 do t[#t+1]=read(base+i) end
 return t,string.format("%02X%02X%02X%02X",t[1],t[2],t[3],t[4])
end
-- IEEE754 decoding without string.unpack, for Lua 5.1
local function floatbe(b)
 local sign=b[1]>=128 and -1 or 1
 local exp=(b[1]%128)*2+math.floor(b[2]/128)
 local fraction=(b[2]%128)*65536+b[3]*256+b[4]
 if exp==255 then return nil end
 if exp==0 then return sign*(fraction/8388608)*2^-126 end
 return sign*(1+fraction/8388608)*2^(exp-127)
end
local function exclusive(path)
 local f=io.open(path,"rb")
 if f then f:close();error("Refusing overwrite "..path) end
 return assert(io.open(path,"wb"),"Cannot create "..path.."; create output directories")
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="bond_position_v1_1_"..sid
local csv=exclusive("output/csv/"..stem.."_timeline.csv")
local marks=exclusive("output/csv/"..stem.."_markers.csv")
local term=exclusive("output/csv/"..stem.."_termination.csv")
local discontinuities=exclusive("output/csv/"..stem.."_discontinuities.csv")
csv:write("session,frame,phase,offset_hex,kseg0_hex,kseg1_hex,float32_be,finite,alias_equal,changed\n")
marks:write("session,frame,phase\n")
term:write("session,frame,reason\n")
discontinuities:write("session,previous_frame,frame,delta\n")
local pointer=assert(io.open("output/sessions/bond_position_v1_1_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local phase,seq,previousFrame="PRESTART",1,nil
local prev={}
local reason="frame_limit"
print("[bond.v1.1] session="..sid.." read-only System Bus")
print("[bond.v1.1] send one phase marker at a time; wait for MARKED before performing action")
local frame=emu.framecount()
for tick=1,MAX_FRAMES do
 frame=emu.framecount()
 if previousFrame and frame~=previousFrame+1 then
  discontinuities:write(table.concat({sid,previousFrame,frame,frame-previousFrame},","),"\n")
  discontinuities:flush()
  reason="timeline_discontinuity"
  break
 end
 previousFrame=frame
 local cmd="output/commands/"..stem.."_"..string.format("%04d",seq)..".txt"
 local f=io.open(cmd,"rb")
 if f then
  local body=f:read("*a");f:close()
  local command=body:match("^SESSION:([^\n]+)\nLABEL:([A-Z0-9_]+)\n$")
  local claimed,label=body:match("^SESSION:([^\n]+)\nLABEL:([A-Z0-9_]+)\n$")
  if claimed~=sid or not allowed[label] then reason="invalid_marker";break end
  phase=label
  marks:write(table.concat({sid,frame,phase},","),"\n");marks:flush()
  print("[bond.v1.1] MARKED "..phase.." frame="..frame)
  seq=seq+1
  if phase=="STOP" then reason="stop";break end
 end
 for _,offset in ipairs(BASES) do
  local b0,h0=raw(0x80000000+offset)
  local b1,h1=raw(0xA0000000+offset)
  local fl=floatbe(b0)
  local value=fl and string.format("%.9g",fl) or ""
  local changed=prev[offset] and prev[offset]~=h0 and 1 or 0
  prev[offset]=h0
  csv:write(string.format("%s,%d,%s,0x%06X,%s,%s,%s,%d,%d,%d\n",sid,frame,phase,offset,h0,h1,value,fl and 1 or 0,h0==h1 and 1 or 0,changed or 0))
 end
 if tick%30==0 then csv:flush() end
 if callable(gui,"text") then
  local b,h=raw(0x800D33EC)
  gui.text(10,40,"Bond v1.1 "..phase.." 0D33EC="..h.." float="..tostring(floatbe(b)))
 end
 emu.frameadvance()
end
term:write(table.concat({sid,frame,reason},","),"\n")
csv:close();marks:close();term:close();discontinuities:close()
print("[bond.v1.1] DONE reason="..reason.." session="..sid)
