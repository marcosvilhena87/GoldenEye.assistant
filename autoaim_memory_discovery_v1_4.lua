-- v1.4 temporal observer. Experimental offsets, read-only, no controller input.
local ROOT="output/"
local DOMAIN=nil -- Explicitly verify and set "RDRAM" in BizHawk.
local EXPECTED_SIZE=nil -- Explicitly verify and set 8388608.
local SAMPLE_EVERY=1
local MAX_FRAMES=36000 -- hard cap: 10 minutes at 60 fps.
local OFFSETS={{0x040A93,"0x040A93"},{0x067D37,"0x067D37"},
 {0x069AAD,"0x069AAD"},{0x0D308B,"0x0D308B"},{0x0D309B,"0x0D309B"}}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
if DOMAIN==nil or EXPECTED_SIZE==nil then
 print("[autoaim.memory.v1.4] Verify DOMAIN and EXPECTED_SIZE manually; stopped.")
 return
end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"RDRAM validation failed")
assert(SAMPLE_EVERY>=1 and MAX_FRAMES>0,"Invalid sampling options")
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local prefix=ROOT.."csv/autoaim_mem_v1_4_"..session
local function create(path,header)
 local probe=io.open(path,"rb")
 if probe then probe:close();error("Existing session file: "..path) end
 local f=assert(io.open(path,"wb"));f:write(header,"\n");f:close()
end
local timeline=prefix.."_timeline.csv"
local events=prefix.."_events.csv"
local markers=prefix.."_markers.csv"
create(timeline,"session,frame,offset_hex,byte,changed")
create(events,"session,frame,offset_hex,old_byte,new_byte")
create(markers,"session,frame,label")
local sf=assert(io.open(ROOT.."sessions/autoaim_mem_v1_4_session.txt","wb"))
sf:write(session,"\n");sf:close()
local previous={}
local index=1
local start=emu.framecount()
print("[autoaim.memory.v1.4] session="..session.." offsets=5 SAMPLE_EVERY="..SAMPLE_EVERY)
print("[autoaim.memory.v1.4] read-only; mark events after setting game state; STOP via sender")
local function append(path,records)
 if #records==0 then return end
 local f=assert(io.open(path,"ab"))
 f:write(table.concat(records,"\n"),"\n");f:close()
end
local function command()
 local path=ROOT.."commands/autoaim_mem_v1_4_"..session.."_"..string.format("%04d",index)..".txt"
 local f=io.open(path,"rb")
 if not f then return false end
 local body=f:read("*a");f:close()
 local label=body:match("^SESSION:"..session.."\nLABEL:([A-Z0-9_]+)\n$")
 if not label or #label>64 then
  print("[autoaim.memory.v1.4] invalid command; stopping safely: "..path)
  return "error"
 end
 append(markers,{session..","..emu.framecount()..","..label})
 print("[autoaim.memory.v1.4] marked "..label.." frame="..emu.framecount())
 index=index+1
 if label=="STOP" then return "stop" end
 return false
end
for tick=1,MAX_FRAMES do
 local status=command()
 if status=="stop" or status=="error" then break end
 if (tick-1)%SAMPLE_EVERY==0 then
  local frame=emu.framecount()
  local readings={}
  local transitions={}
  for _,entry in ipairs(OFFSETS) do
   local addr,hex=entry[1],entry[2]
   local byte=memory.read_u8(addr,DOMAIN)
   assert(type(byte)=="number" and byte>=0 and byte<=255,"Invalid RDRAM byte at "..hex)
   local old=previous[hex]
   local changed=(old~=nil and old~=byte) and 1 or 0
   readings[#readings+1]=session..","..frame..","..hex..","..byte..","..changed
   if changed==1 then
    transitions[#transitions+1]=session..","..frame..","..hex..","..old..","..byte
   end
   previous[hex]=byte
  end
  append(timeline,readings)
  append(events,transitions)
 end
 emu.frameadvance()
end
print("[autoaim.memory.v1.4] FINISHED session="..session.." frame="..emu.framecount())
