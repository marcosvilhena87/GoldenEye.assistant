-- GoldenEye Auto-Aim Memory Discovery v1.1: read-only controlled sequence.
-- Operator MUST verify domain and ROM/core. No assumed auto-aim offsets.
local ROOT = "output/"
local DOMAIN = nil -- Set explicitly after memory.getmemorydomainsize("RDRAM") check, e.g. "RDRAM"
local EXPECTED_SIZE = nil -- Set observed value, e.g. 8388608
local MAX_BYTES = 8 * 1024 * 1024
local LABELS = {"A1","A_STABLE","B","B_STABLE","A2","CONTROL_A"}

assert(memory and memory.getmemorydomainsize and memory.read_u8 and emu and emu.frameadvance, "Required BizHawk APIs unavailable")
if memory.getmemorydomainlist then
 print("[autoaim.memory.v1.1] Reported domains:")
 for _, d in ipairs(memory.getmemorydomainlist()) do
  local ok, n=pcall(memory.getmemorydomainsize,d)
  print("  "..tostring(d).." size="..(ok and tostring(n) or "unavailable"))
 end
end
if not DOMAIN or not EXPECTED_SIZE then
 print("[autoaim.memory.v1.1] Configure DOMAIN and EXPECTED_SIZE explicitly in script; no capture started.")
 return
end
assert(type(DOMAIN)=="string" and DOMAIN~="" and DOMAIN~="System Bus", "Invalid domain")
assert(type(EXPECTED_SIZE)=="number" and EXPECTED_SIZE>0 and EXPECTED_SIZE<=MAX_BYTES and EXPECTED_SIZE%1==0, "Invalid size")
local size=memory.getmemorydomainsize(DOMAIN)
assert(size==EXPECTED_SIZE, "Domain size mismatch")
local function check(path)
 local f=io.open(path,"rb")
 if not f then error("Missing output folder: "..path.."; run python tools/prepare_output.py") end
 f:close()
end
-- Output directory validated by session-file creation below; no .gitkeep dependency.
local function write(path,content)
 local f=assert(io.open(path,"wb"));f:write(content);f:close()
end
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
write(ROOT.."sessions/autoaim_mem_v1_1_session.txt",session.."\n")
print("[autoaim.memory.v1.1] session="..session.." domain="..DOMAIN.." size="..size)
print("[autoaim.memory.v1.1] Requests: output/commands/autoaim_mem_v1_1_"..session.."_NN.txt")
local idx=1
local manifest=ROOT.."csv/autoaim_mem_v1_1_manifest.csv"
local function capture(label)
 local path=ROOT.."archive/autoaim_mem_v1_1_"..session.."_"..label..".bin"
 local f=assert(io.open(path,"wb"))
 local ok,err=pcall(function()
  local buf={}
  for i=0,size-1 do
   local b=memory.read_u8(i,DOMAIN)
   assert(type(b)=="number" and b>=0 and b<=255 and b%1==0, "Invalid byte at "..i)
   buf[#buf+1]=string.char(b)
   if #buf==4096 then f:write(table.concat(buf));buf={} end
  end
  if #buf>0 then f:write(table.concat(buf)) end
 end)
 f:close()
 if not ok then os.remove(path);error(err) end
 local mf=io.open(manifest,"r");local first=mf==nil;if mf then mf:close() end
 mf=assert(io.open(manifest,"a"))
 if first then mf:write("session,label,frame,domain,size,path\n") end
 mf:write(session,",",label,",",emu.framecount(),",",DOMAIN,",",size,",",path,"\n")
 mf:close()
 print("[autoaim.memory.v1.1] captured "..label.." frame="..emu.framecount())
end
while true do
 if idx<=#LABELS then
  local request=ROOT.."commands/autoaim_mem_v1_1_"..session.."_"..string.format("%02d",idx)..".txt"
  local f=io.open(request,"rb")
  if f then
   local content=f:read("*a");f:close()
   local sid,label=content:match("^SESSION:([^\r\n]+)[\r\n]+SNAPSHOT:([^\r\n]+)")
   if sid~=session or label~=LABELS[idx] then
    print("[autoaim.memory.v1.1] INVALID request "..request.."; expected "..LABELS[idx].."; correct file manually")
    -- Do not advance; bad request remains for operator review.
   else
    local ok,err=pcall(capture,label)
    if ok then idx=idx+1
    else print("[autoaim.memory.v1.1] capture FAILED: "..tostring(err));break end
   end
  end
 elseif idx==#LABELS+1 then
  print("[autoaim.memory.v1.1] COMPLETE session="..session)
  idx=idx+1
 end
 emu.frameadvance()
end
