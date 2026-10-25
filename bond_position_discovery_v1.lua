-- Bond Position Discovery v1: observation only, no RAM writes.
local DOMAIN="RDRAM"
local BASE=0x0D33E8
local LAST=0x0D33F0
local PREFIX="./output/csv/bond_position_v1_"
local clock=os.date("!%Y%m%dT%H%M%SZ")
local path=PREFIX..clock..".csv"
local f,err=io.open(path,"w")
assert(f,"Create output/csv first: "..tostring(err))
assert(type(memory.read_u8)=="function","BizHawk memory.read_u8 unavailable")
local domains=memory.getmemorydomainlist()
local found=false
for _,d in ipairs(domains) do if d==DOMAIN then found=true end end
assert(found,"RDRAM domain unavailable")
assert(memory.getmemorydomainsize(DOMAIN)>LAST,"RDRAM too small")
f:write("frame,label,offset_hex,raw_be_hex,u16_be,u16_le,changed_since_previous\n")
local frame=0
local label="BASELINE"
local previous={}
local function read16be(addr)
 local a=memory.read_u8(addr,DOMAIN)
 local b=memory.read_u8(addr+1,DOMAIN)
 return a*256+b,b*256+a,string.format("%02X%02X",a,b)
end
console.log("[bond_position_v1] logging "..path)
console.log("[bond_position_v1] Labels: edit local label via Lua restart per phase; record interventions in separate notes.")
while true do
 frame=emu.framecount()
 for addr=BASE,LAST-2,2 do
  local be,le,hex=read16be(addr)
  local changed=(previous[addr]~=nil and previous[addr]~=hex) and 1 or 0
  f:write(string.format("%d,%s,0x%06X,%s,%d,%d,%d\n",frame,label,addr,hex,be,le,changed))
  previous[addr]=hex
 end
 if frame%60==0 then f:flush() end
 gui.text(10,40,string.format("Bond v1 READ ONLY | 0D33EC=%d",select(1,read16be(0x0D33EC))))
 emu.frameadvance()
end
