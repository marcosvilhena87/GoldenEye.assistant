-- Horizontal Correction v1.6: experimental read-only temporal probe.
local ROOT="output/"
local DOMAIN=nil -- Set to "RDRAM" only after verifying in BizHawk
local EXPECTED_SIZE=nil -- Set to 8388608 after verification
local MAX_FRAMES=36000
-- Explicitly verified only. These are raw probe windows, not identified headings.
-- Optional verified independent camera heading address. Never guess this value.
local CAMERA_HEADING_ADDRESS=nil
local CAMERA_HEADING_BYTES=4
-- Experimental v1.1 leads, NOT validated correction or aligned float fields.
local WINDOWS={{0x0D3995,"0x0D3995"},{0x0D3D3D,"0x0D3D3D"}}
-- Record neighboring aligned 4-byte windows to test framing rather than assume LE floats.
for _,address in ipairs({0x0D3995,0x0D3D3D}) do
 local aligned=address-(address%4)
 for delta=-4,4,4 do
  local a=aligned+delta
  WINDOWS[#WINDOWS+1]={a,string.format("0x%06X",a)}
 end
end
if CAMERA_HEADING_ADDRESS then
 assert(type(CAMERA_HEADING_ADDRESS)=="number" and CAMERA_HEADING_ADDRESS%1==0 and CAMERA_HEADING_BYTES==4,"Invalid camera config")
 WINDOWS[#WINDOWS+1]={CAMERA_HEADING_ADDRESS,string.format("0x%06X",CAMERA_HEADING_ADDRESS)}
end
local ACTIONS={FIXED_AIM_DISABLED=true,FIXED_AIM_ENABLED=true,FIXED_AIM_WITH_TARGET=true,FIXED_AIM_NO_TARGET=true,NEW_SCENE_BASELINE=true,FIXED_NO_TARGET=true,FIXED_AIM_LEFT=true,FIXED_AIM_RIGHT=true,FIXED_AIM_CENTER=true,TURN_LEFT_NO_TARGET=true,TURN_RIGHT_NO_TARGET=true,TURN_LEFT_AIM_OFF=true,TURN_RIGHT_AIM_OFF=true,REST_AFTER_TURN=true}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.framecount and emu.frameadvance,"Missing APIs")
if not DOMAIN or not EXPECTED_SIZE then print("[horizontal.v1.6] Set verified DOMAIN and EXPECTED_SIZE first");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Unexpected memory domain")
for _,w in ipairs(WINDOWS) do assert(w[1]>=0 and w[1]+3<EXPECTED_SIZE,"Window outside RDRAM") end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local prefix=ROOT.."csv/horizontal_v1_6_"..sid
local function create(path,header)
 local f=io.open(path,"rb");if f then f:close();error("Refuse overwrite "..path) end
 f=assert(io.open(path,"wb"));f:write(header,"\n");f:close()
end
local timeline,events,markers=prefix.."_timeline.csv",prefix.."_events.csv",prefix.."_markers.csv"
local termination=prefix.."_termination.csv"
local discontinuities=prefix.."_discontinuities.csv"
local manifest=prefix.."_manifest.csv"
create(timeline,"session,sample_index,frame,offset_hex,raw_hex,changed")
create(events,"session,sample_index,frame,offset_hex,old_hex,new_hex")
create(markers,"session,sample_index,frame,label,action,phase")
create(termination,"session,sample_index,frame,reason,active_action,ticks")
create(discontinuities,"session,sample_index,previous_frame,frame,delta,active_action")
create(manifest,"session,domain,domain_size,max_frames,source_version,meaning")
local mf=assert(io.open(manifest,"ab"));mf:write(sid..","..DOMAIN..","..EXPECTED_SIZE..","..MAX_FRAMES..",v1.6,experimental_raw_windows_not_headings\n");mf:close()
local ptr=assert(io.open(ROOT.."sessions/horizontal_v1_6_session.txt","wb"));ptr:write(sid,"\n");ptr:close()
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
local reason="frame_limit"
local ticks=0
local last_sample=0
local previous_frame=nil
print("[horizontal.v1.6] session="..sid.." two raw windows; manually verify camera state for EVERY trial; max_frames="..MAX_FRAMES)
for tick=1,MAX_FRAMES do
 ticks=tick
 local frame=emu.framecount()
 if previous_frame~=nil and frame~=previous_frame+1 then
  local delta=frame-previous_frame
  append(discontinuities,{sid..","..tick..","..previous_frame..","..frame..","..delta..","..tostring(active or "NONE")})
  reason="timeline_discontinuity"
  print("[horizontal.v1.6] DISCONTINUITY sample_index="..tick.." previous="..previous_frame.." current="..frame.." active_action="..tostring(active))
  break
 end
 previous_frame=frame
 last_sample=tick
 local cmd=ROOT.."commands/horizontal_v1_6_"..sid.."_"..string.format("%04d",index)..".txt"
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
  if not label then reason="invalid_marker"; print("[horizontal.v1.6] Invalid/out-of-order request "..cmd);break end
  append(markers,{sid..","..tick..","..frame..","..label..","..action..","..phase})
  print("[horizontal.v1.6] marked "..label.." frame="..frame)
  index=index+1
 end
 local samples,changes={},{}
 for _,entry in ipairs(WINDOWS) do
  local value=word(entry[1]);local old=previous[entry[2]]
  local changed=(old~=nil and old~=value) and 1 or 0
  samples[#samples+1]=sid..","..tick..","..frame..","..entry[2]..","..value..","..changed
  if changed==1 then changes[#changes+1]=sid..","..tick..","..frame..","..entry[2]..","..old..","..value end
  previous[entry[2]]=value
 end
 append(timeline,samples);append(events,changes)
 if stop then reason="stop";break end
 emu.frameadvance()
end
append(termination,{sid..","..last_sample..","..emu.framecount()..","..reason..","..tostring(active or "NONE")..","..ticks})
print("[horizontal.v1.6] FINISHED session="..sid.." reason="..reason.." active_action="..tostring(active))
