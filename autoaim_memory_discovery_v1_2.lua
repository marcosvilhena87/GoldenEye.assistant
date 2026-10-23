-- Auto-Aim Memory Discovery v1.2: read-only targeted candidate monitoring.
-- Configure domain and size after observing them in BizHawk. NO game RAM writes.
local ROOT="output/"
local DOMAIN=nil -- Explicitly set "RDRAM" after verifying direct domain access
local EXPECTED_SIZE=nil -- Explicitly set 8388608 if verified again
local WATCHLIST=ROOT.."commands/autoaim_mem_v1_2_watchlist.csv"
local LABELS={"ON1","ON_STABLE","OFF1","OFF_STABLE","ON2","MENU_NO_CHANGE","OFF2","ON3"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance,"Missing BizHawk APIs")
if not DOMAIN or not EXPECTED_SIZE then print("[autoaim.memory.v1.2] Set DOMAIN and EXPECTED_SIZE manually; stopped.");return end
assert(DOMAIN=="RDRAM" and EXPECTED_SIZE==8388608,"Explicit RDRAM 8 MiB confirmation required")
assert(memory.getmemorydomainsize(DOMAIN)==EXPECTED_SIZE,"Domain size mismatch")
local f=assert(io.open(WATCHLIST,"r"),"Run python tools/prepare_autoaim_mem_v1_2.py first")
local header=f:read("*l");assert(header=="offset_hex,on_byte,off_byte","Unexpected watchlist header")
local offsets,seen={},{}
for line in f:lines() do
 local hex,on,off=line:match("^(0x%x+),(%d+),(%d+)$")
 assert(hex and on and off,"Malformed watchlist row")
 local n=tonumber(hex);on=tonumber(on);off=tonumber(off)
 assert(n and n>=0 and n<EXPECTED_SIZE and not seen[n],"Invalid or duplicate offset")
 assert(on>=0 and on<=255 and off>=0 and off<=255 and on~=off,"Invalid expected bytes")
 seen[n]=true;offsets[#offsets+1]={offset=n,hex=hex,on=on,off=off}
end
f:close()
assert(#offsets>0 and #offsets<=1024,"Expected 1..1024 observed offsets")
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local function write(path,s) local z=assert(io.open(path,"wb"));z:write(s);z:close()end
write(ROOT.."sessions/autoaim_mem_v1_2_session.txt",session.."\n")
local manifest=ROOT.."csv/autoaim_mem_v1_2_manifest.csv"
local samples=ROOT.."csv/autoaim_mem_v1_2_samples.csv"
local function append(path,header,row)
 local f=io.open(path,"r");local isnew=not f;if f then f:close()end
 f=assert(io.open(path,"a"));if isnew then f:write(header,"\n")end
 f:write(row,"\n");f:close()
end
local index=1
print("[autoaim.memory.v1.2] session="..session.." domain="..DOMAIN.." candidate_count="..#offsets)
print("[autoaim.memory.v1.2] IMPORTANT: states are operator-confirmed; commands alone do not change auto-aim")
local function capture(label)
 local frame=emu.framecount()
 local lines={}
 for _,v in ipairs(offsets) do
  local b=memory.read_u8(v.offset,DOMAIN)
  assert(type(b)=="number" and b>=0 and b<=255,"Invalid byte at "..v.hex)
  lines[#lines+1]=session..","..label..","..frame..","..DOMAIN..","..v.hex..","..b
 end
 local out=assert(io.open(samples,"a"))
 if out:seek("end")==0 then out:write("session,label,frame,domain,offset_hex,byte\n")end
 out:write(table.concat(lines,"\n"),"\n");out:close()
 append(manifest,"session,label,frame,domain,count",session..","..label..","..frame..","..DOMAIN..","..#offsets)
 print("[autoaim.memory.v1.2] captured "..label.." frame="..frame.." bytes="..#offsets)
end
while true do
 if index<=#LABELS then
  local path=ROOT.."commands/autoaim_mem_v1_2_"..session.."_"..string.format("%02d",index)..".txt"
  local q=io.open(path,"r")
  if q then
   local req=q:read("*a");q:close()
   local sid,label=req:match("^SESSION:([^\r\n]+)[\r\n]+SNAPSHOT:([^\r\n]+)")
   if sid==session and label==LABELS[index] then
    local ok,err=pcall(capture,label)
    if not ok then print("[autoaim.memory.v1.2] FATAL capture error: "..tostring(err));break end
    index=index+1
   else
    print("[autoaim.memory.v1.2] INVALID request: "..path);break
   end
  end
 elseif index==#LABELS+1 then
  print("[autoaim.memory.v1.2] COMPLETE session="..session);index=index+1
 end
 emu.frameadvance()
end
