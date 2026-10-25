-- Bond Position Discovery v1.0.3 - read-only, emulator API diagnostics
local DOMAIN_OVERRIDE=nil -- set to an EXACT domain name after inspection if needed
local BASE=0x0D33E8
local LAST=0x0D33F0
local function available(t,k)
  if t==nil then return false end
  local ok,v=pcall(function() return t[k] end)
  return ok and v~=nil and (type(v)=="function" or type(v)=="userdata")
end
local function report(s) if available(console,"log") then console.log(s) else print(s) end end
assert(available(memory,"getmemorydomainlist") and available(memory,"getmemorydomainsize"),
  "Cannot enumerate memory domains; check the BizHawk Lua Console")
local domains=memory.getmemorydomainlist()
local names={}
local eligible={}
local selected=nil
for _,name in ipairs(domains) do
  local ok,size=pcall(memory.getmemorydomainsize,name)
  local desc=tostring(name).."("..(ok and tostring(size) or "?").." bytes)"
  names[#names+1]=desc
  if ok and type(size)=="number" and size>=LAST then
    if name=="RDRAM" then selected=name end
    if type(name)=="string" and name:upper():find("RDRAM",1,true) then
      eligible[#eligible+1]=name
    end
  end
end
report("[bond.position.v1.0.3] Available memory domains: "..table.concat(names,", "))
if DOMAIN_OVERRIDE then
  selected=nil
  for _,name in ipairs(domains) do
    if name==DOMAIN_OVERRIDE and memory.getmemorydomainsize(name)>=LAST then selected=name end
  end
  assert(selected,"DOMAIN_OVERRIDE not found or insufficient size: "..tostring(DOMAIN_OVERRIDE))
elseif not selected then
  if #eligible==1 then selected=eligible[1] end
end
assert(selected,
  "No unique RDRAM domain. Inspect console domain list; if Cheat Search mapping is confirmed, set DOMAIN_OVERRIDE to the EXACT listed name.")
assert(available(memory,"read_u8") or available(memory,"readbyte"),
  "Neither memory.read_u8 nor memory.readbyte available")
local reader=available(memory,"read_u8") and memory.read_u8 or memory.readbyte
local read8=function(addr) return reader(addr,selected) end
local source="memory/"..selected
report("[bond.position.v1.0.3] Selected domain="..selected..
       " size="..tostring(memory.getmemorydomainsize(selected)))
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
report("[bond.position.v1.0.3] read-only; source="..source.." file="..path)
report("[bond.position.v1.0.3] label BASELINE is generic; annotate external interventions with frames.")
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
