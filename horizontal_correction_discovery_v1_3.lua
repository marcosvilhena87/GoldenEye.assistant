-- Horizontal Correction v1.2: experimental read-only temporal probe.
local ROOT="output/"
local DOMAIN=nil -- Set to "RDRAM" only after verifying in BizHawk
local EXPECTED_SIZE=nil -- Set to 8388608 after verification
local MAX_FRAMES=36000
-- Experimental v1.1 leads, NOT validated correction or aligned float fields.
local WINDOWS={{0x0D3995,"0x0D3995"},{0x0D3D3D,"0x0D3D3D"}}
local ACTIONS={FIXED_CAMERA_ON_TARGET=true,FIXED_CAMERA_OFF_TARGET=true,FIXED_CAMERA_NO_TARGET=true,TURN_CAMERA_NO_TARGET=true,FIXED_CAMERA_CONTROL=true}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"Missing APIs")
if not DOMAIN or not EXPECTED_SIZE then print("[horizontal.v1.3] Set verified DOMAIN and EXPECTED_SIZE first");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Unexpected memory domain")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local prefix=ROOT.."csv/horizontal_v1_3_"..sid
local function create(path,header)
 local f=io.open(path,"rb");if f then f:close();error("Refuse overwrite "..path) end
 f=assert(io.open(path,"wb"));f:write(header,"\n");f:close()
end
local timeline,events,markers=prefix.."_timeline.csv",prefix.."_events.csv",prefix.."_markers.csv"
create(timeline,"session,frame,offset_hex,raw_hex,changed")
create(events,"session,frame,offset_hex,old_hex,new_hex")
create(markers,"session,frame,label,action,phase")
local ptr=assert(io.open(ROOT.."sessions/horizontal_v1_3_session.txt","wb"));ptr:write(sid,"\n");ptr:close()
local function append(path,rows)
 if #rows==0 then return end
 local f=assert(io.open(path,"ab"));f:write(table.concat(rows,"\n"),"\n");f:close()
end
local function word(addr)
 local b={}
 for k=0,3 do
  local v=memory.read_u8(addr+k,DOMAIN)
  assert(type(v)=="number" and v%1==0 and v>=0 and v<=255,"Invalid byte")
  b[#b+1]=string.format("%02X",v)
 end
 return table.concat(b)
end
local index,active,previous=1,nil,{}
print("[horizontal.v1.3] session="..sid.." two raw windows; manually verify camera state for EVERY trial; max_frames="..MAX_FRAMES)
for tick=1,MAX_FRAMES do
 local frame=emu.framecount()
 local cmd=ROOT.."commands/horizontal_v1_3_"..sid.."_"..string.format("%04d",index)..".txt"
 local f=io.open(cmd,"rb")
 local stop=false
 if f then
  local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  local phase,action
  if label=="STOP" and active==nil then phase="STOP";action="NONE";stop=true
  elseif label then
   phase,action=label:match("^(BEGIN)_(.+)$")
   if phase=="BEGIN" and ACTIONS[action] and active==nil then active=action
   else
    phase,action=label:match("^(END)_(.+)$")
    if phase=="END" and ACTIONS[action] and active==action then active=nil
    else label=nil end
   end
  end
  if not label then print("[horizontal.v1.3] Invalid/out-of-order request "..cmd);break end
  append(markers,{sid..","..frame..","..label..","..action..","..phase})
  print("[horizontal.v1.3] marked "..label.." frame="..frame)
  index=index+1
 end
 local samples,changes={},{}
 for _,entry in ipairs(WINDOWS) do
  local value=word(entry[1]);local old=previous[entry[2]]
  local changed=(old~=nil and old~=value) and 1 or 0
  samples[#samples+1]=sid..","..frame..","..entry[2]..","..value..","..changed
  if changed==1 then changes[#changes+1]=sid..","..frame..","..entry[2]..","..old..","..value end
  previous[entry[2]]=value
 end
 append(timeline,samples);append(events,changes)
 if stop then break end
 emu.frameadvance()
end
print("[horizontal.v1.3] FINISHED session="..sid.." active_action="..tostring(active))
