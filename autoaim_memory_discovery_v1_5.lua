-- Auto-Aim v1.5 semantic-field experiment: read-only, bracketed interventions.
local ROOT="output/"
local DOMAIN=nil -- verify in BizHawk, then set "RDRAM"
local EXPECTED_SIZE=nil -- verify in BizHawk, then set 8388608
local MAX_FRAMES=36000
local OFFSETS={{0x040A93,"0x040A93"},{0x067D37,"0x067D37"},{0x069AAD,"0x069AAD"},{0x0D308B,"0x0D308B"},{0x0D309B,"0x0D309B"}}
local ACTIONS={AUTOAIM_OFF=true,AUTOAIM_ON=true,MENU_ONLY=true,OTHER_OPTION=true,NO_TARGET=true,TARGET_VISIBLE=true,WEAPON_CHANGE=true,LEVEL_RESTART=true}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"Missing BizHawk APIs")
if not DOMAIN or not EXPECTED_SIZE then print("[autoaim.v1.5] Configure DOMAIN and EXPECTED_SIZE; stopped");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"RDRAM size/domain mismatch")
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local prefix=ROOT.."csv/autoaim_mem_v1_5_"..sid
local function create(path,header)
 local f=io.open(path,"rb");if f then f:close();error("Refuse overwrite: "..path) end
 f=assert(io.open(path,"wb"));f:write(header,"\n");f:close()
end
local timeline=prefix.."_timeline.csv"
local transitions=prefix.."_events.csv"
local markers=prefix.."_markers.csv"
create(timeline,"session,frame,offset_hex,byte,changed")
create(transitions,"session,frame,offset_hex,old_byte,new_byte")
create(markers,"session,frame,label,action,phase")
local pointer=assert(io.open(ROOT.."sessions/autoaim_mem_v1_5_session.txt","wb"));pointer:write(sid,"\n");pointer:close()
local function append(path,records)
 if #records==0 then return end
 local f=assert(io.open(path,"ab"));f:write(table.concat(records,"\n"),"\n");f:close()
end
local index,previous,active=1,{},nil
print("[autoaim.v1.5] session="..sid.." offsets=5; read-only; bracket each action BEGIN before manual change and END after")
for tick=1,MAX_FRAMES do
 local frame=emu.framecount()
 local path=ROOT.."commands/autoaim_mem_v1_5_"..sid.."_"..string.format("%04d",index)..".txt"
 local f=io.open(path,"rb")
 local stop=false
 if f then
  local body=f:read("*a");f:close()
  local label=body:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  local phase,action="",""
  if label=="STOP" and active==nil then phase="STOP";action="NONE";stop=true
  elseif label then
   phase,action=label:match("^(BEGIN)_(.+)$")
   if phase and ACTIONS[action] and active==nil then active=action
   else
    phase,action=label:match("^(END)_(.+)$")
    if phase and ACTIONS[action] and active==action then active=nil
    else label=nil end
   end
  end
  if not label then
   print("[autoaim.v1.5] Invalid or out-of-order marker; halting without capture: "..path)
   break
  end
  append(markers,{sid..","..frame..","..label..","..action..","..phase})
  print("[autoaim.v1.5] marked "..label.." frame="..frame)
  index=index+1
 end
 -- Markers and samples share a frame; Python treats BEGIN/END as boundaries.
 local rows,events={},{}
 for _,entry in ipairs(OFFSETS) do
  local byte=memory.read_u8(entry[1],DOMAIN)
  assert(type(byte)=="number" and byte>=0 and byte<=255,"Invalid byte")
  local old=previous[entry[2]]
  local changed=(old~=nil and old~=byte) and 1 or 0
  rows[#rows+1]=sid..","..frame..","..entry[2]..","..byte..","..changed
  if changed==1 then events[#events+1]=sid..","..frame..","..entry[2]..","..old..","..byte end
  previous[entry[2]]=byte
 end
 append(timeline,rows);append(transitions,events)
 if stop then break end
 emu.frameadvance()
end
print("[autoaim.v1.5] FINISHED session="..sid.." active_action="..tostring(active))
