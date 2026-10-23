-- Auto-Aim Memory Discovery v1.3. Read-only RDRAM; fresh session CSVs.
-- Set both values only after confirming the BizHawk domain and size.
local ROOT = "output/"
local DOMAIN = nil -- Set "RDRAM" after verification.
local EXPECTED_SIZE = nil -- Set 8388608 after verification.
local LABELS = {"ON_BASE","ON_STABLE","OFF1","OFF_STABLE","ON2","MENU_CONTROL","OTHER_OPTION_CONTROL","NO_TARGET_ON"}
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance,
       "Missing BizHawk APIs")
if not DOMAIN or not EXPECTED_SIZE then
  print("[autoaim.memory.v1.3] Set DOMAIN and EXPECTED_SIZE manually; stopped.")
  return
end
assert(DOMAIN == "RDRAM" and EXPECTED_SIZE == 8388608, "Verify RDRAM 8 MiB")
assert(memory.getmemorydomainsize(DOMAIN) == EXPECTED_SIZE, "Domain mismatch")
-- Candidate provenance: observed v1.2.1 session 20261023T200459Z_70077; unvalidated.
local offsets = {
  {offset=0x040A93,hex="0x040A93"},
  {offset=0x067D37,hex="0x067D37"},
  {offset=0x069AAD,hex="0x069AAD"},
  {offset=0x0D308B,hex="0x0D308B"},
  {offset=0x0D309B,hex="0x0D309B"},
}
assert(#offsets==5,"Unexpected watchlist")
local session=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local manifest=ROOT.."csv/autoaim_mem_v1_3_manifest_"..session..".csv"
local samples=ROOT.."csv/autoaim_mem_v1_3_samples_"..session..".csv"
local function write_new(path, data)
  local check=io.open(path,"rb")
  if check then check:close();error("Refusing overwrite: "..path) end
  local f=assert(io.open(path,"wb"))
  f:write(data);f:close()
end
write_new(manifest,"session,label,frame,domain,count\n")
write_new(samples,"session,label,frame,domain,offset_hex,byte\n")
local pointer=assert(io.open(ROOT.."sessions/autoaim_mem_v1_3_session.txt","wb"))
pointer:write(session,"\n");pointer:close()
local index=1
local last_invalid=nil
print("[autoaim.memory.v1.3] NEW INDEPENDENT RUN: restart emulator/game before second run. session="..session.." candidate_count="..#offsets.." domain="..DOMAIN)
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
  print("[autoaim.memory.v1.3] captured "..label.." frame="..frame.." bytes="..#offsets)
end
while true do
  if index<=#LABELS then
    local path=ROOT.."commands/autoaim_mem_v1_3_"..session.."_"..string.format("%02d",index)..".txt"
    local f=io.open(path,"rb")
    if f then
      local request=f:read("*a");f:close()
      local expected="SESSION:"..session.."\nSNAPSHOT:"..LABELS[index].."\n"
      if request==expected then
        local ok,err=pcall(capture,LABELS[index])
        if not ok then
          print("[autoaim.memory.v1.3] CAPTURE FAILURE (manual inspection required): "..tostring(err))
          break
        end
        index=index+1
      else
        -- Do not abort on transient/incomplete commands. Never capture invalid input.
        if last_invalid~=path then print("[autoaim.memory.v1.3] request invalid/incomplete; awaiting correction: "..path);last_invalid=path end
        -- An invalid permanent file must be moved aside manually before retrying.
      end
    end
  elseif index==#LABELS+1 then
    print("[autoaim.memory.v1.3] COMPLETE session="..session)
    index=index+1
  end
  emu.frameadvance()
end
