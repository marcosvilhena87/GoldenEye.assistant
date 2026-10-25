-- Soldier #1 Coordinate Discovery v1.8.5 (BizHawk; READ ONLY)
-- Controlled RDRAM snapshots: no game-memory writes, no XYZ claims.
local DOMAIN="RDRAM"
local MAX_BYTES=8*1024*1024
local LABELS={BASELINE=true,BOND_ROTATE=true,BOND_MOVE=true,SOLDIER_MOVE=true,SOLDIER_FREEZE=true,NEW_SAVE=true,STOP=true}
assert(memory and memory.getmemorydomainsize and memory.read_u8 and emu and emu.frameadvance and emu.framecount,"BizHawk APIs unavailable")
local size=memory.getmemorydomainsize(DOMAIN)
assert(type(size)=="number" and size==MAX_BYTES,"Expected an observed 8MiB RDRAM domain; inspect emulator configuration")
local function exists(path) local f=io.open(path,"rb");if f then f:close();return true end return false end
local function create(path)
 assert(not exists(path),"File exists: "..path)
 return assert(io.open(path,"wb"),"Create output folders before starting")
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local stem="soldier_coordinate_v1_8_5_"..sid
local session=assert(io.open("output/sessions/soldier_coordinate_v1_8_5_session.txt","wb"))
session:write(sid,"\n");session:close()
local manifest=create("output/csv/"..stem.."_manifest.csv")
manifest:write("session,label,frame,domain,size,path\n");manifest:flush()
local termination=create("output/csv/"..stem.."_termination.csv")
termination:write("session,frame,reason\n");termination:flush()
local function snapshot(label,frame)
 local path="output/archive/"..stem.."_"..label..".bin"
 local out=create(path)
 local ok,err=pcall(function()
  local buf={}
  for pos=0,size-1 do
   local v=memory.read_u8(pos,DOMAIN)
   assert(type(v)=="number" and v>=0 and v<=255 and v%1==0,"invalid RDRAM byte "..pos)
   buf[#buf+1]=string.char(v)
   if #buf==4096 then out:write(table.concat(buf));buf={} end
  end
  if #buf>0 then out:write(table.concat(buf)) end
 end)
 out:close()
 if not ok then os.remove(path);error(err) end
 manifest:write(string.format("%s,%s,%d,%s,%d,%s\n",sid,label,frame,DOMAIN,size,path));manifest:flush()
 print("[soldier.v1.8.5] CAPTURED "..label.." frame="..frame)
end
print("[soldier.v1.8.5] session="..sid.." read-only domain="..DOMAIN.." bytes="..size)
local index=1
local previous=nil
local reason="frame_limit"
local frame=emu.framecount()
for tick=1,36000 do
 frame=emu.framecount()
 if previous and frame~=previous+1 then reason="timeline_discontinuity";break end
 previous=frame
 local path=string.format("output/commands/%s_%04d.txt",stem,index)
 local f=io.open(path,"rb")
 if f then
  local body=f:read("*a");f:close()
  local label=body:gsub("^\239\187\191",""):gsub("\r\n","\n"):gsub("\r","\n"):match("^LABEL:([A-Z_0-9]+)\n?$")
  if not LABELS[label] then
   print("[soldier.v1.8.5] INVALID "..path.." content="..string.format("%q",body))
   reason="invalid_marker";break
  end
  print("[soldier.v1.8.5] MARKED "..label.." frame="..frame)
  if label=="STOP" then reason="stop";break end
  local ok,err=pcall(snapshot,label,frame)
  if not ok then reason="snapshot_failed";print("[soldier.v1.8.5] FAILED "..tostring(err));break end
  index=index+1
 end
 emu.frameadvance()
end
termination:write(string.format("%s,%d,%s\n",sid,frame,reason))
manifest:close();termination:close()
print("[soldier.v1.8.5] DONE "..reason.." session="..sid)
