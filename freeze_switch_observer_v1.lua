-- Freeze switch observer v1. Read-only. BizHawk Lua 5.1.
-- Candidate byte: 0x02C90C in RDRAM. Values and behavior not yet validated.
local DOMAIN = "RDRAM"
local ADDRESS = 0x02C90C
local SIZE = 8388608
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance, "Missing API")
assert(memory.getmemorydomainsize(DOMAIN) == SIZE and ADDRESS < SIZE, "Unverified RDRAM")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local path="output/csv/freeze_switch_v1_"..sid..".csv"
local check=io.open(path,"rb")
if check then check:close();error("Refusing overwrite") end
local f=assert(io.open(path,"wb"))
f:write("session,frame,offset_hex,value_dec,value_hex,transition\n")
f:flush()
local prev,prevframe=nil,nil
print("[freeze.switch] read-only; manually enable/disable cheat; CSV="..path)
for i=1,18000 do
 local frame=emu.framecount()
 if prevframe and frame ~= prevframe+1 then
  print("[freeze.switch] frame discontinuity; stopping")
  break
 end
 local value=memory.read_u8(ADDRESS,DOMAIN)
 local changed=(prev==nil or value~=prev)
 if changed then
  f:write(table.concat({sid,frame,"0x02C90C",value,string.format("0x%02X",value),prev==nil and "initial" or "changed"},","),"\n")
  f:flush()
  print(string.format("[freeze.switch] frame=%d value=%d (0x%02X)",frame,value,value))
 end
 prev=value
 prevframe=frame
 emu.frameadvance()
end
f:close()
print("[freeze.switch] finished")
