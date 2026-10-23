-- Horizontal Correction Discovery v1: read-only RDRAM full snapshots; NO assumed field offsets.
local ROOT="output/"
local DOMAIN=nil -- verify then set "RDRAM"
local EXPECTED_SIZE=nil -- verify then set 8388608
local LABELS={"ON_NO_TARGET","ON_LEFT","ON_CENTER","ON_RIGHT","OFF_LEFT","OFF_CENTER","OFF_RIGHT","ON_LEFT_REPEAT"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount,"BizHawk API unavailable")
if not DOMAIN or not EXPECTED_SIZE then print("[horizontal.v1] Configure verified domain/size first");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608 and memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Unexpected domain")
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local manifest=ROOT.."csv/horizontal_v1_manifest_"..session..".csv"
local function create(path,body)
 local f=io.open(path,"rb");if f then f:close();error("Refuse overwrite: "..path) end
 f=assert(io.open(path,"wb"));f:write(body);f:close()
end
create(manifest,"session,label,frame,domain,size,path\n")
local pointer=assert(io.open(ROOT.."sessions/horizontal_v1_session.txt","wb"));pointer:write(session,"\n");pointer:close()
print("[horizontal.v1] session="..session.." read-only snapshots=8; set scene manually for each label")
local index=1
local function capture(label)
 local path=ROOT.."archive/horizontal_v1_"..session.."_"..label..".bin"
 local f=io.open(path,"rb");if f then f:close();error("Refuse overwrite "..path) end
 f=assert(io.open(path,"wb"))
 local ok,err=pcall(function()
  local chunk={}
  for i=0,EXPECTED_SIZE-1 do
   local byte=memory.read_u8(i,DOMAIN)
   assert(type(byte)=="number" and byte>=0 and byte<=255 and byte%1==0,"Invalid byte at "..i)
   chunk[#chunk+1]=string.char(byte)
   if #chunk==4096 then f:write(table.concat(chunk));chunk={} end
  end
  if #chunk>0 then f:write(table.concat(chunk)) end
 end)
 f:close()
 if not ok then os.remove(path);error(err) end
 f=assert(io.open(manifest,"ab"))
 f:write(session,",",label,",",emu.framecount(),",",DOMAIN,",",EXPECTED_SIZE,",",path,"\n");f:close()
 print("[horizontal.v1] captured "..label.." frame="..emu.framecount())
end
while true do
 if index<=#LABELS then
  local path=ROOT.."commands/horizontal_v1_"..session.."_"..string.format("%02d",index)..".txt"
  local f=io.open(path,"rb")
  if f then
   local req=f:read("*a");f:close()
   if req=="SESSION:"..session.."\nSNAPSHOT:"..LABELS[index].."\n" then
    local ok,err=pcall(capture,LABELS[index])
    if not ok then print("[horizontal.v1] capture failed: "..tostring(err));break end
    index=index+1
   else print("[horizontal.v1] Invalid request; stop and investigate: "..path);break end
  end
 elseif index==#LABELS+1 then
  print("[horizontal.v1] COMPLETE session="..session);index=index+1
 end
 emu.frameadvance()
end
