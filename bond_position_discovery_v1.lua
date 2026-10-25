-- Bond Position Discovery v1.0.2 - read-only, emulator API diagnostics
local DOMAIN="RDRAM"
local BASE=0x0D33E8
local LAST=0x0D33F0
local function available(t,k)
  if t==nil then return false end
  local ok,v=pcall(function() return t[k] end)
  return ok and v~=nil and (type(v)=="function" or type(v)=="userdata")
end
local function report(s) if available(console,"log") then console.log(s) else print(s) end end
local read8,source
if available(memory,"read_u8") and available(memory,"getmemorydomainlist") then
  local found=false
  for _,name in ipairs(memory.getmemorydomainlist()) do
    if name==DOMAIN then found=true end
  end
  assert(found,"RDRAM missing: confirm domain name in BizHawk Lua Console")
  assert(available(memory,"getmemorydomainsize") and memory.getmemorydomainsize(DOMAIN)>=LAST,
    "RDRAM size too small or memory domain size API missing")
  read8=function(addr) return memory.read_u8(addr,DOMAIN) end
  source="memory.read_u8/RDRAM"
elseif available(memory,"readbyte") and available(memory,"getmemorydomainlist") then
  local found=false
  for _,name in ipairs(memory.getmemorydomainlist()) do if name==DOMAIN then found=true end end
  assert(found,"RDRAM domain missing")
  read8=function(addr) return memory.readbyte(addr,DOMAIN) end
  source="memory.readbyte/RDRAM"
elseif available(mainmemory,"read_u8") then
  -- Main memory may or may not be the Cheat Search RDRAM domain.
  error("Only mainmemory.read_u8 available. Refusing to assume its offset mapping equals Cheat Search RDRAM. Confirm emulator/core and domain before proceeding.")
else
  error("No compatible RDRAM byte-read API. memory.read_u8="..tostring(memory and type(memory.read_u8))..
    ", memory.readbyte="..tostring(memory and type(memory.readbyte))..
    ", mainmemory.read_u8="..tostring(mainmemory and type(mainmemory.read_u8))..
    ". Load this script from BizHawk Lua Console with N64 ROM running; verify API availability.")
end
assert(type(emu)=="table" and available(emu,"frameadvance") and available(emu,"framecount"),"emu frame API unavailable")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local path="output/csv/bond_position_v1_"..sid..".csv"
local exists=io.open(path,"rb")
if exists then exists:close();error("Refusing overwrite: "..path) end
local f,err=io.open(path,"wb")
assert(f,"Create output/csv in repository root: "..tostring(err))
f:write("session,frame,label,offset_hex,raw_be_hex,u16_be,u16_le,changed_since_previous\n")
f:flush()
local previous={}
local function read16(addr)
 local a,b=read8(addr),read8(addr+1)
 assert(type(a)=="number" and type(b)=="number" and a>=0 and a<256 and b>=0 and b<256,"Invalid byte read")
 return a*256+b,b*256+a,string.format("%02X%02X",a,b)
end
report("[bond.position.v1.0.1] read-only; source="..source.." file="..path)
report("[bond.position.v1.0.1] label BASELINE is generic; annotate external interventions with frames.")
while true do
 local frame=emu.framecount()
 for addr=BASE,LAST-2,2 do
  local be,le,raw=read16(addr)
  local changed=previous[addr] and previous[addr]~=raw and 1 or 0
  f:write(string.format("%s,%d,BASELINE,0x%06X,%s,%d,%d,%d\n",sid,frame,addr,raw,be,le,changed or 0))
  previous[addr]=raw
 end
 if frame%60==0 then f:flush() end
 if available(gui,"text") then gui.text(10,40,"Bond v1 READ ONLY | 0D33EC="..tostring(select(1,read16(0x0D33EC)))) end
 emu.frameadvance()
end
