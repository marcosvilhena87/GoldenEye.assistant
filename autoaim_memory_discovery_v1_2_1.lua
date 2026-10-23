-- Auto-Aim Memory Discovery v1.2.1. Read-only RDRAM; fresh session CSVs.
-- Set both values only after confirming the BizHawk domain and size.
local ROOT = "output/"
local DOMAIN = nil -- Set "RDRAM" after verification.
local EXPECTED_SIZE = nil -- Set 8388608 after verification.
local LABELS = {"ON1","ON_STABLE","OFF1","OFF_STABLE","ON2","MENU_NO_CHANGE","OFF2","ON3"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance,
       "Missing BizHawk APIs")
if not DOMAIN or not EXPECTED_SIZE then
  print("[autoaim.memory.v1.2.1] Set DOMAIN and EXPECTED_SIZE manually; stopped.")
  return
end
assert(DOMAIN == "RDRAM" and EXPECTED_SIZE == 8388608, "Verify RDRAM 8 MiB")
assert(memory.getmemorydomainsize(DOMAIN) == EXPECTED_SIZE, "Domain mismatch")
local source = assert(io.open(ROOT.."commands/autoaim_mem_v1_2_watchlist.csv", "r"),
                      "Run prepare_autoaim_mem_v1_2.py")
assert(source:read("*l") == "offset_hex,on_byte,off_byte", "Invalid watchlist header")
local offsets,seen = {},{}
for line in source:lines() do
  local hex,on,off = line:match("^(0x%x+),(%d+),(%d+)$")
  assert(hex, "Malformed watchlist")
  local n = tonumber(hex)
  on,off = tonumber(on),tonumber(off)
  assert(n and n>=0 and n<EXPECTED_SIZE and not seen[n], "Duplicate/bad offset")
  assert(on>=0 and on<=255 and off>=0 and off<=255 and on~=off, "Bad expected values")
  seen[n]=true
  offsets[#offsets+1]={offset=n,hex=hex}
end
source:close()
assert(#offsets==131, "v1.2.1 sender requires 131 candidates; stop if different")
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local manifest=ROOT.."csv/autoaim_mem_v1_2_1_manifest_"..session..".csv"
local samples=ROOT.."csv/autoaim_mem_v1_2_1_samples_"..session..".csv"
local function write_new(path, data)
  local check=io.open(path,"rb")
  if check then check:close();error("Refusing overwrite: "..path) end
  local f=assert(io.open(path,"wb"))
  f:write(data);f:close()
end
write_new(manifest,"session,label,frame,domain,count\n")
write_new(samples,"session,label,frame,domain,offset_hex,byte\n")
write_new(ROOT.."sessions/autoaim_mem_v1_2_1_session.txt",session.."\n")
local index=1
print("[autoaim.memory.v1.2.1] session="..session.." candidate_count="..#offsets.." domain="..DOMAIN)
local function capture(label)
  local frame=emu.framecount()
  local lines={}
  for _,v in ipairs(offsets) do
    local b=memory.read_u8(v.offset,DOMAIN)
    assert(type(b)=="number" and b>=0 and b<=255,"Bad byte "..v.hex)
    lines[#lines+1]=session..","..label..","..frame..","..DOMAIN..","..v.hex..","..b
  end
  local f=assert(io.open(samples,"ab"));f:write(table.concat(lines,"\n"),"\n");f:close()
  f=assert(io.open(manifest,"ab"))
  f:write(session..","..label..","..frame..","..DOMAIN..","..#offsets.."\n")
  f:close()
  print("[autoaim.memory.v1.2.1] captured "..label.." frame="..frame.." bytes="..#offsets)
end
while true do
  if index<=#LABELS then
    local path=ROOT.."commands/autoaim_mem_v1_2_1_"..session.."_"..string.format("%02d",index)..".txt"
    local f=io.open(path,"rb")
    if f then
      local request=f:read("*a");f:close()
      local expected="SESSION:"..session.."\nSNAPSHOT:"..LABELS[index].."\n"
      if request==expected then
        local ok,err=pcall(capture,LABELS[index])
        if not ok then
          print("[autoaim.memory.v1.2.1] CAPTURE FAILURE (manual inspection required): "..tostring(err))
          break
        end
        index=index+1
      else
        -- Do not abort on transient/incomplete commands. Never capture invalid input.
        print("[autoaim.memory.v1.2.1] request invalid/incomplete; awaiting correction: "..path)
        -- An invalid permanent file must be moved aside manually before retrying.
      end
    end
  elseif index==#LABELS+1 then
    print("[autoaim.memory.v1.2.1] COMPLETE session="..session)
    index=index+1
  end
  emu.frameadvance()
end
