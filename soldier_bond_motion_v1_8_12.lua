-- Soldier Spatial Structure Correlation v1.8.12 (BizHawk, READ ONLY).
-- Offsets are investigative; no X/Z or stable entity identity assumed.
local D="RDRAM"
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
assert(memory.getmemorydomainsize(D)==8388608,"RDRAM must be exactly 8 MiB")
local seeds={0x06A128,0x06A154,0x06A15C,0x1F1914,0x1F1970,0x1F1980,0x1F1988,0x1F1AE8,0x1F1AF0,0x1F1B48,0x1F1B4C,0x1F1B50,0x1F1B54,0x1F1B58,0x1F1B5C,0x1F1B60,0x1F1B64,0x20F400,0x20F408,0x20F580,0x20F594,0x20F5AC,0x20F728,0x20F730,0x20F744,0x20F74C,0x20F754,0x20F75C,0x20F760,0x20F768,0x20F76C,0x20F774,0x06D248,0x06D250,0x0D33EC,0x0D33F0,0x0D33F4}
local offsets,seen={},{}
for _,s in ipairs(seeds) do
 for o=s-8,s+8,4 do
  if o>=0 and o+3<8388608 and not seen[o] then seen[o]=true;offsets[#offsets+1]=o end
 end
end
table.sort(offsets)
local LABELS={BASELINE=true,FREEZE_REQUEST_ON=true,FREEZE_CONFIRMED=true,STILL_BEFORE=true,ROTATE_LEFT=true,STILL_AFTER_LEFT=true,ROTATE_RIGHT=true,STILL_AFTER_RIGHT=true,TRANSLATE_FORWARD=true,STILL_AFTER_FORWARD=true,TRANSLATE_BACK=true,STILL_AFTER_BACK=true,ROTATE_REPEAT=true,STILL_FINAL=true,STOP=true}
local function create(path,header)
 local old=io.open(path,"rb");assert(not old,"Output already exists: "..path)
 local f=assert(io.open(path,"wb"),"Create output folders first")
 f:write(header,"\n");f:flush();return f
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local stem="soldier_motion_v1_8_12_"..sid
local trace=create("output/csv/"..stem.."_timeline.csv","session,frame,phase,offset_hex,raw_be,changed")
local marks=create("output/csv/"..stem.."_markers.csv","session,frame,label")
local endfile=create("output/csv/"..stem.."_termination.csv","session,frame,reason")
local s=assert(io.open("output/sessions/soldier_motion_v1_8_12_session.txt","wb"));s:write(sid,"\n");s:close()
local prev,phase,seq,last={}, "PRESTART",1,nil
local reason="frame_limit"
local frame=emu.framecount()
print("[soldier.motion.v1.8.12] session="..sid.." fields="..#offsets.." READ ONLY")
for tick=1,24000 do
 frame=emu.framecount()
 if last and frame~=last+1 then reason="timeline_discontinuity";break end
 last=frame
 local request=string.format("output/commands/%s_%04d.txt",stem,seq)
 local c=io.open(request,"rb")
 if c then
  local b=c:read("*a");c:close()
  local label=b:gsub("^\239\187\191",""):gsub("\r\n","\n"):gsub("\r","\n"):match("^LABEL:([A-Z_0-9]+)\n?$")
  if not LABELS[label] then reason="invalid_marker";print("[soldier.motion.v1.8.12] INVALID "..request);break end
  phase=label;marks:write(string.format("%s,%d,%s\n",sid,frame,label));marks:flush()
  print("[soldier.motion.v1.8.12] MARKED "..label.." frame="..frame)
  seq=seq+1
  if label=="STOP" then reason="stop";break end
 end
 for _,off in ipairs(offsets) do
  local b={}
  for i=0,3 do b[#b+1]=memory.read_u8(off+i,D) end
  local raw=string.format("%02X%02X%02X%02X",b[1],b[2],b[3],b[4])
  local changed=prev[off] and prev[off]~=raw and 1 or 0
  trace:write(string.format("%s,%d,%s,0x%06X,%s,%d\n",sid,frame,phase,off,raw,changed))
  prev[off]=raw
 end
 if tick%15==0 then trace:flush() end
 emu.frameadvance()
end
endfile:write(string.format("%s,%d,%s\n",sid,frame,reason))
trace:close();marks:close();endfile:close()
print("[soldier.motion.v1.8.12] DONE "..reason.." session="..sid)
