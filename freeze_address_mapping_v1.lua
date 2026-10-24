-- Freeze Address Mapping v1: read-only cross-domain alias experiment, Lua 5.1.
-- No RDRAM assumption: this N64 core exposes System Bus only.
local DOMAIN="System Bus"
local OFF=0x02C90C
local candidates={
 {name="physical_same",addr=OFF},
 {name="kseg0_alias",addr=0x80000000+OFF},
 {name="kseg1_alias",addr=0xA0000000+OFF}
}
local labels={OFF1=true,ON1=true,OFF2=true,ON2=true,STOP=true}
assert(memory and memory.getmemorydomainlist and memory.read_u8 and emu and emu.frameadvance and emu.framecount,"BizHawk Lua API missing")
local present=false
for _,name in ipairs(memory.getmemorydomainlist()) do if name==DOMAIN then present=true end end
assert(present,"System Bus unavailable; stop")
local function exists(p)
 local f=io.open(p,"rb");if f then f:close();return true end;return false
end
local function newfile(p)
 assert(not exists(p),"Refusing overwrite "..p)
 return assert(io.open(p,"wb"))
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="freeze_address_v1_"..sid
local csv=newfile("output/csv/"..stem.."_timeline.csv")
csv:write("session,frame,phase,candidate,address_hex,read_ok,value_u8,value_hex,error\n");csv:flush()
local marks=newfile("output/csv/"..stem.."_markers.csv")
marks:write("session,frame,phase\n");marks:flush()
local pointer=assert(io.open("output/sessions/freeze_address_v1_session.txt","wb"));pointer:write(sid,"\n");pointer:close()
local phase="UNLABELED"
local index=1
local previous=nil
local reason="frame_limit"
print("[freeze.address.v1] session="..sid.." read-only on "..DOMAIN)
print("[freeze.address.v1] Run python tools/send_freeze_address_v1.py OFF1, ON1, OFF2, ON2, STOP")
for tick=1,36000 do
 local frame=emu.framecount()
 if previous and frame~=previous+1 then reason="timeline_discontinuity";break end
 previous=frame
 local cmd=string.format("output/commands/%s_%04d.txt",stem,index)
 if exists(cmd) then
  local f=assert(io.open(cmd,"rb"));local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  if not label or not labels[label] then reason="invalid_marker";break end
  phase=label
  marks:write(sid..","..frame..","..phase.."\n");marks:flush()
  print("[freeze.address.v1] marked "..phase.." frame="..frame)
  index=index+1
  if phase=="STOP" then reason="stop";break end
 end
 for _,c in ipairs(candidates) do
  local ok,value=pcall(memory.read_u8,c.addr,DOMAIN)
  local val=ok and tostring(value) or ""
  local hex=(ok and type(value)=="number") and string.format("%02X",value) or ""
  local err=ok and "" or tostring(value):gsub("[\r\n,]"," ")
  csv:write(table.concat({sid,frame,phase,c.name,string.format("0x%08X",c.addr),
    ok and "1" or "0",val,hex,err},","),"\n")
 end
 if frame%60==0 then csv:flush() end
 emu.frameadvance()
end
csv:flush();csv:close();marks:close()
print("[freeze.address.v1] finished reason="..reason.." session="..sid)
