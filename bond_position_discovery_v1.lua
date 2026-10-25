-- Bond Position Discovery v1.0.4 - read-only System Bus KSEG0/KSEG1
local OFFSET_FIRST=0x0D33E8
local OFFSET_END=0x0D33F0 -- exclusive
local BUS="System Bus"
local KSEG0=0x80000000
local KSEG1=0xA0000000
local function callable(t,k)
 if t==nil then return false end
 local ok,v=pcall(function() return t[k] end)
 return ok and v~=nil and (type(v)=="function" or type(v)=="userdata")
end
local function say(s)
 if callable(console,"log") then console.log(s) else print(s) end
end
assert(callable(memory,"getmemorydomainlist"),"memory domain enumeration unavailable")
local found=false
for _,name in ipairs(memory.getmemorydomainlist()) do
 if name==BUS then found=true end
end
assert(found,"System Bus unavailable (no RDRAM assumption)")
assert(callable(memory,"read_u8") or callable(memory,"readbyte"),"byte-read API unavailable")
assert(callable(emu,"framecount") and callable(emu,"frameadvance"),"frame API unavailable")
local readfunc=callable(memory,"read_u8") and memory.read_u8 or memory.readbyte
local function read(addr)
 local ok,v=pcall(readfunc,addr,BUS)
 assert(ok and type(v)=="number" and v>=0 and v<=255 and v%1==0,
 "invalid System Bus read at "..string.format("0x%08X",addr)..": "..tostring(v))
 return v
end
local function word(addr)
 local a,b=read(addr),read(addr+1)
 return string.format("%02X%02X",a,b),a*256+b,b*256+a
end
local initial0=word(KSEG0+0x0D33EC)
local initial1=word(KSEG1+0x0D33EC)
say("[bond.position.v1.0.4] 0D33EC KSEG0="..initial0.." KSEG1="..initial1..
 " (alias comparison is not proof of Cheat Search correspondence)")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local path="output/csv/bond_position_v1_"..sid..".csv"
local exists=io.open(path,"rb")
if exists then exists:close();error("Refusing overwrite "..path) end
local out,err=io.open(path,"wb")
assert(out,"Create output/csv under repository root: "..tostring(err))
out:write("session,frame,phase,offset_hex,kseg0_hex,kseg1_hex,kseg0_u16_be,kseg0_u16_le,kseg1_u16_be,kseg1_u16_le,alias_equal,kseg0_changed\n")
out:flush()
local prev={}
say("[bond.position.v1.0.4] recording read-only: "..path)
say("[bond.position.v1.0.4] phase=UNMARKED; note intervention frames externally")
while true do
 local frame=emu.framecount()
 for offset=OFFSET_FIRST,OFFSET_END-2,2 do
  local a,be,le=word(KSEG0+offset)
  local b,be1,le1=word(KSEG1+offset)
  local changed=prev[offset] and prev[offset]~=a and 1 or 0
  prev[offset]=a
  out:write(string.format("%s,%d,UNMARKED,0x%06X,%s,%s,%d,%d,%d,%d,%d,%d\n",
    sid,frame,offset,a,b,be,le,be1,le1,(a==b and 1 or 0),changed or 0))
 end
 if frame%60==0 then out:flush() end
 if callable(gui,"text") then
  local raw,be=word(KSEG0+0x0D33EC)
  gui.text(10,40,string.format("Bond v1.0.4 | System Bus KSEG0 0D33EC=%d (%s)",be,raw))
 end
 emu.frameadvance()
end
