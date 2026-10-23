-- GoldenEye Auto-Aim Memory Discovery v1 — explicitly selected domain, read-only snapshots.
-- Uses BizHawk memory.read_u8(address, domain) after user-selected domain is confirmed.
local ROOT="output/"
local function write(path,data)
 local f=assert(io.open(path,"wb"));f:write(data);f:close()
end
local function checkdir() assert(io.open(ROOT.."sessions/.gitkeep","rb") or io.open(ROOT.."sessions/autoaim_v3_1_session.txt","rb") or io.open(ROOT.."sessions/autoaim_mem_v1_session.txt","rb"),"Run python tools/prepare_output.py before starting") end
local function now()return os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())end
local function domains()
 assert(memory and memory.getmemorydomainlist and memory.getmemorydomainsize and memory.read_u8,"Required BizHawk memory APIs unavailable")
 local list=memory.getmemorydomainlist()
 print("[autoaim.memory.v1] Available domains (choose explicitly, no assumed domain):")
 for _,name in ipairs(list) do
  local ok,n=pcall(memory.getmemorydomainsize,name)
  print("  "..tostring(name).."  size="..(ok and tostring(n) or "unavailable"))
 end
end
domains()
-- Operator must edit both variables below AFTER reviewing printed domains and ROM/core identity.
local DOMAIN=nil
local EXPECTED_SIZE=nil
local MAX_BYTES=8*1024*1024
if not DOMAIN or not EXPECTED_SIZE then
 print("[autoaim.memory.v1] Discovery only. Set DOMAIN and EXPECTED_SIZE explicitly, then rerun.")
 return
end
assert(type(DOMAIN)=="string" and DOMAIN~="","Set domain")
assert(type(EXPECTED_SIZE)=="number" and EXPECTED_SIZE>0 and EXPECTED_SIZE<=MAX_BYTES and EXPECTED_SIZE%1==0,"Invalid size/max 8 MiB")
local size=memory.getmemorydomainsize(DOMAIN)
assert(size==EXPECTED_SIZE,"Domain size mismatch; aborting")
local session=now()
write(ROOT.."sessions/autoaim_mem_v1_session.txt",session.."\n")
print("[autoaim.memory.v1] session="..session.." domain="..DOMAIN.." size="..size)
print("[autoaim.memory.v1] Snapshot command file: output/commands/autoaim_mem_v1_request.txt")
local last_command=""
local seen={}
local order={"A1","B","A2"}
local next_idx=1
local function safe_name(s)return s:match("^[A-Z][A-Z0-9_]*$")~=nil end
local function capture(label)
 assert(label==order[next_idx],"Expected "..tostring(order[next_idx])..", got "..label)
 local chunks={};local part={}
 for i=0,size-1 do
  local b=memory.read_u8(i,DOMAIN)
  assert(type(b)=="number" and b>=0 and b<=255,"Invalid byte at "..i)
  part[#part+1]=string.char(b)
  if #part>=4096 then chunks[#chunks+1]=table.concat(part);part={} end
 end
 if #part>0 then chunks[#chunks+1]=table.concat(part) end
 local path=ROOT.."archive/autoaim_mem_v1_"..session.."_"..label..".bin"
 write(path,table.concat(chunks))
 local manifest=ROOT.."csv/autoaim_mem_v1_manifest.csv"
 local f=io.open(manifest,"r");local new=f==nil;if f then f:close() end
 f=assert(io.open(manifest,"a"))
 if new then f:write("session,label,frame,domain,size,path\n") end
 f:write(session,",",label,",",emu.framecount(),",",DOMAIN,",",size,",",path,"\n");f:close()
 print("[autoaim.memory.v1] captured "..label.." frame="..emu.framecount())
 next_idx=next_idx+1
end
while true do
 local f=io.open(ROOT.."commands/autoaim_mem_v1_request.txt","r")
 if f then
  local s=f:read("*a");f:close()
  if s~=last_command and s~="" then
   last_command=s
   local sid,label=s:match("^SESSION:([^\r\n]+)[\r\n]+SNAPSHOT:([^\r\n]+)")
   if sid~=session then print("[autoaim.memory.v1] ignored wrong session")
   elseif not label or not safe_name(label) then print("[autoaim.memory.v1] invalid label")
   else
    local ok,err=pcall(capture,label)
    if not ok then print("[autoaim.memory.v1] aborted: "..tostring(err)) end
   end
  end
 end
 emu.frameadvance()
end
