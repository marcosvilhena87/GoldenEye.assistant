-- Soldier Spatial Structure Correlation v1.9.2 (BizHawk, READ ONLY).
-- Offsets are investigative; no X/Z or stable entity identity assumed.
local D="RDRAM"
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
assert(memory.getmemorydomainsize(D)==8388608,"RDRAM must be exactly 8 MiB")
local seeds={0x0D33D8,0x0D33E0,0x0D33E8,0x0D33EC,0x0D33F0,0x0D33F4,0x0D33F8,0x0D33FC,0x0D3400,0x0D3404,0x0D340C,0x0D3414,0x0D3998,0x0D39A0,0x0D3D40,0x0D3D48}
local offsets,seen={},{}
-- Include unaligned byte candidates explicitly in addition to aligned float32 windows.
local byte_fields={0x0D36F4,0x0D3720,0x040A93,0x0D308B,0x0D309B}
for _,s in ipairs(seeds) do
 for o=s-8,s+8,4 do
  if o>=0 and o+3<8388608 and not seen[o] then seen[o]=true;offsets[#offsets+1]=o end
 end
end
for _,o in ipairs(byte_fields) do if not seen[o] then seen[o]=true;offsets[#offsets+1]=o end end
table.sort(offsets)
local LABELS={BASELINE_STILL=true,TURN_LEFT_90=true,HOLD_90=true,TURN_LEFT_180=true,HOLD_180=true,TURN_LEFT_270=true,HOLD_270=true,TURN_LEFT_360=true,HOLD_360=true,TURN_RIGHT_270=true,HOLD_R270=true,TURN_RIGHT_180=true,HOLD_R180=true,TURN_RIGHT_90=true,HOLD_R90=true,TURN_RIGHT_0=true,HOLD_ORIGIN=true,MOVE_FORWARD=true,HOLD_MOVE=true,STOP=true}
local function create(path,header)
 local old=io.open(path,"rb");assert(not old,"Output already exists: "..path)
 local f=assert(io.open(path,"wb"),"Create output folders first")
 f:write(header,"\n");f:flush();return f
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local stem="bond_heading_v1_9_2_"..sid
local trace=create("output/csv/"..stem.."_timeline.csv","session,frame,phase,offset_hex,raw_be,changed")
local marks=create("output/csv/"..stem.."_markers.csv","session,frame,label")
local endfile=create("output/csv/"..stem.."_termination.csv","session,frame,reason")
local s=assert(io.open("output/sessions/bond_heading_v1_9_2_session.txt","wb"));s:write(sid,"\n");s:close()
local prev,phase,seq,last={}, "PRESTART",1,nil
local reason="frame_limit"
local frame=emu.framecount()
print("[bond.heading.v1.9.2] session="..sid.." fields="..#offsets.." READ ONLY")
for tick=1,60000 do
 frame=emu.framecount()
 if last and frame~=last+1 then reason="timeline_discontinuity";break end
 last=frame
 local request=string.format("output/commands/%s_%04d.txt",stem,seq)
 local c=io.open(request,"rb")
 if c then
  local b=c:read("*a");c:close()
  local label=b:gsub("^\239\187\191",""):gsub("\r\n","\n"):gsub("\r","\n"):match("^LABEL:([A-Z_0-9]+)\n?$")
  if not LABELS[label] then reason="invalid_marker";print("[bond.heading.v1.9.2] INVALID "..request);break end
  phase=label;marks:write(string.format("%s,%d,%s\n",sid,frame,label));marks:flush()
  print("[bond.heading.v1.9.2] MARKED "..label.." frame="..frame)
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
print("[bond.heading.v1.9.2] DONE "..reason.." session="..sid)
