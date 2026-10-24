-- Spatial Position Confirmation v1.7.4 — eight provisional RAW 4-byte windows.
-- Read-only; no coordinate, type, heading or target meaning is validated.
local ROOT="output/"
local DOMAIN=nil -- Set "RDRAM" after verifying in BizHawk
local EXPECTED_SIZE=nil -- Set 8388608 after verifying
local MAX_FRAMES=36000
local OFFSETS={0x05FCB4,0x05FCD4,0x0D61C4,0x0E79C4,0x1F1E88,0x1F1E8C,0x1F1E90,0x2EBCE4}
local ACTIONS={REST_BASELINE=true,MOVE_LEFT=true,REST_AFTER_LEFT=true,
 MOVE_RIGHT=true,REST_AFTER_RIGHT=true,MOVE_FORWARD=true,REST_AFTER_FORWARD=true,
 MOVE_BACK=true,REST_AFTER_BACK=true,ROTATE_ONLY=true,REST_AFTER_ROTATION=true}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"Missing BizHawk APIs")
if DOMAIN==nil or EXPECTED_SIZE==nil then print("[spatial.v1.7.4] Verify and configure DOMAIN and EXPECTED_SIZE");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Unexpected domain")
for _,a in ipairs(OFFSETS) do assert(a>=0 and a+3<EXPECTED_SIZE,"Out-of-range probe") end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local base=ROOT.."csv/spatial_v1_7_4_"..sid
local function create(path,header)
 local existing=io.open(path,"rb");if existing then existing:close();error("Refuse overwrite "..path) end
 local f=assert(io.open(path,"wb"));f:write(header,"\n");f:close()
end
local timeline=base.."_timeline.csv"
local events=base.."_events.csv"
local markers=base.."_markers.csv"
local termination=base.."_termination.csv"
local discontinuities=base.."_discontinuities.csv"
local manifest=base.."_manifest.csv"
create(timeline,"session,sample_index,frame,action,offset_hex,raw_hex,changed")
create(events,"session,sample_index,frame,action,offset_hex,old_hex,new_hex")
create(markers,"session,sample_index,frame,label,action,phase")
create(termination,"session,sample_index,frame,reason,active_action,ticks")
create(discontinuities,"session,sample_index,previous_frame,frame,delta,active_action")
create(manifest,"session,domain,domain_size,max_frames,source_version,meaning")
local f=assert(io.open(manifest,"ab"));f:write(sid..","..DOMAIN..","..EXPECTED_SIZE..","..MAX_FRAMES..",v1.7.4,experimental_raw_windows_not_positions\n");f:close()
local ptr=assert(io.open(ROOT.."sessions/spatial_v1_7_4_session.txt","wb"));ptr:write(sid,"\n");ptr:close()
local function append(path,rows)
 if #rows==0 then return end
 local f=assert(io.open(path,"ab"));f:write(table.concat(rows,"\n"),"\n");f:close()
end
local function word(a)
 local b={}
 for k=0,3 do
  local v=memory.read_u8(a+k,DOMAIN)
  assert(type(v)=="number" and v%1==0 and v>=0 and v<=255,"Bad byte")
  b[#b+1]=string.format("%02X",v)
 end
 return table.concat(b)
end
local active=nil
local command_index=1
local prev={}
local previous_frame=nil
local reason="frame_limit"
local ticks=0
local last_sample=0
print("[spatial.v1.7.4] session="..sid.." tracking eight RAW windows, no memory writes")
for tick=1,MAX_FRAMES do
 ticks=tick
 local frame=emu.framecount()
 if previous_frame and frame~=previous_frame+1 then
  append(discontinuities,{sid..","..tick..","..previous_frame..","..frame..","..(frame-previous_frame)..","..(active or "NONE")})
  reason="timeline_discontinuity"
  break
 end
 previous_frame=frame
 last_sample=tick
 local cmd=ROOT.."commands/spatial_v1_7_4_"..sid.."_"..string.format("%04d",command_index)..".txt"
 local cf=io.open(cmd,"rb")
 local stop=false
 if cf then
  local content=cf:read("*a");cf:close()
  local label=content:match("^SESSION:"..sid.."\nLABEL:([A-Z0-9_]+)\n$")
  local phase,action
  if label=="STOP" and not active then phase="STOP";action="NONE";stop=true
  elseif label then
   phase,action=label:match("^(BEGIN)_(.+)$")
   if phase=="BEGIN" and ACTIONS[action] and not active then active=action
   else
    phase,action=label:match("^(END)_(.+)$")
    if phase=="END" and ACTIONS[action] and active==action then active=nil
    else label=nil end
   end
  end
  if not label then
   reason="invalid_marker"
   print("[spatial.v1.7.4] Invalid marker at "..cmd)
   break
  end
  append(markers,{sid..","..tick..","..frame..","..label..","..action..","..phase})
  print("[spatial.v1.7.4] marked "..label.." frame="..frame)
  command_index=command_index+1
 end
 local samples,changes={},{}
 for _,a in ipairs(OFFSETS) do
  local key=string.format("0x%06X",a)
  local raw=word(a)
  local old=prev[key]
  local changed=(old and old~=raw) and 1 or 0
  local action=active or "NONE"
  samples[#samples+1]=sid..","..tick..","..frame..","..action..","..key..","..raw..","..changed
  if changed==1 then changes[#changes+1]=sid..","..tick..","..frame..","..action..","..key..","..old..","..raw end
  prev[key]=raw
 end
 append(timeline,samples)
 append(events,changes)
 if stop then reason="stop";break end
 emu.frameadvance()
end
append(termination,{sid..","..last_sample..","..emu.framecount()..","..reason..","..(active or "NONE")..","..ticks})
print("[spatial.v1.7.4] FINISHED session="..sid.." reason="..reason.." active="..(active or "NONE"))
