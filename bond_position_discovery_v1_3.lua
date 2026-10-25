-- Bond Position Discovery v1.3; read-only, BizHawk NLua
local BUS="System Bus"
local OFF={0x0D33E8,0x0D33EC,0x0D33F0,0x0D33F4}
local MAX=36000
local LABELS={BASELINE=true,TARGET_EC=true,TARGET_F4=true,WRITE_PRE=true,WRITE_APPLIED=true,WRITE_OBSERVE=true,STOP=true}
local function has(t,k)
 if not t then return false end
 local ok,v=pcall(function() return t[k] end)
 return ok and v~=nil and (type(v)=="function" or type(v)=="userdata")
end
assert(has(memory,"getmemorydomainlist") and has(memory,"read_u8"),"Memory API unavailable")
assert(has(emu,"framecount") and has(emu,"frameadvance"),"Frame API unavailable")
local okbus=false
for _,n in ipairs(memory.getmemorydomainlist()) do if n==BUS then okbus=true end end
assert(okbus,"System Bus absent")
local function byte(addr)
 local ok,v=pcall(memory.read_u8,addr,BUS)
 assert(ok and type(v)=="number" and v>=0 and v<=255 and v%1==0,"Invalid read at "..string.format("%08X",addr))
 return v
end
local function sample(addr)
 local b={}
 for j=0,3 do b[j+1]=byte(addr+j) end
 local raw=string.format("%02X%02X%02X%02X",b[1],b[2],b[3],b[4])
 local e=(b[1]%128)*2+math.floor(b[2]/128)
 local mant=(b[2]%128)*65536+b[3]*256+b[4]
 local sg=b[1]>=128 and -1 or 1
 local v=nil
 if e==0 then v=sg*(mant/8388608)*2^-126
 elseif e<255 then v=sg*(1+mant/8388608)*2^(e-127) end
 return raw,v
end
local function make(path,header)
 local exists=io.open(path,"rb")
 if exists then exists:close();error("File exists "..path) end
 local fp,err=io.open(path,"wb")
 assert(fp,"Create output/csv, output/commands, output/sessions: "..tostring(err))
 fp:write(header,"\n");fp:flush();return fp
end
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(emu.framecount())
local stem="bond_position_v1_3_"..sid
local base="output/csv/"..stem
local timeline=make(base.."_timeline.csv","session,frame,phase,target,event,offset_hex,kseg0_hex,kseg1_hex,float32_be,finite,alias_equal,changed")
local markers=make(base.."_markers.csv","session,frame,label,target,event")
local events=make(base.."_events.csv","session,frame,offset_hex,event,previous_hex,current_hex,delta_float")
local termination=make(base.."_termination.csv","session,frame,reason")
local discontinuity=make(base.."_discontinuities.csv","session,previous_frame,frame,delta")
local pointer=assert(io.open("output/sessions/bond_position_v1_3_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local last={}
local target="NONE"
local phase="PRESTART"
local seq=1
local reason="frame_limit"
local previous_frame=nil
print("[bond.v1.3] session="..sid.." READ ONLY; choose target; WRITE_APPLIED is an observation marker, not an automatic write")
local frame=emu.framecount()
for tick=1,MAX do
 frame=emu.framecount()
 if previous_frame and frame~=previous_frame+1 then
  discontinuity:write(table.concat({sid,previous_frame,frame,frame-previous_frame},","),"\n")
  reason="timeline_discontinuity";break
 end
 previous_frame=frame
 local marker_event=""
 local cmd=string.format("output/commands/%s_%04d.txt",stem,seq)
 local f=io.open(cmd,"rb")
 if f then
  local body=f:read("*a");f:close()
  local session,label=body:match("^SESSION:([^\n]+)\nLABEL:([A-Z_0-9]+)\n$")
  if session~=sid or not LABELS[label] then reason="invalid_marker";break end
  phase=label;marker_event=label
  if label=="TARGET_EC" then target="0x0D33EC" end
  if label=="TARGET_F4" then target="0x0D33F4" end
  markers:write(table.concat({sid,frame,label,target,"operator_marker_not_physical_proof"},","),"\n");markers:flush()
  print("[bond.v1.3] MARKED "..label.." frame="..frame)
  seq=seq+1
  if label=="STOP" then reason="stop";break end
 end
 for _,offset in ipairs(OFF) do
  local h0,v=sample(0x80000000+offset)
  local h1=sample(0xA0000000+offset)
  local old=last[offset]
  local changed=old and old.h~=h0 and 1 or 0
  local val=v and string.format("%.9g",v) or ""
  local delta=(old and old.v and v) and string.format("%.9g",v-old.v) or ""
  timeline:write(string.format("%s,%d,%s,%s,%s,0x%06X,%s,%s,%s,%d,%d,%d\n",sid,frame,phase,target,marker_event,offset,h0,h1,val,v and 1 or 0,h0==h1 and 1 or 0,changed or 0))
  if changed==1 then
   events:write(string.format("%s,%d,0x%06X,change,%s,%s,%s\n",sid,frame,offset,old.h,h0,delta))
  end
  last[offset]={h=h0,v=v}
 end
 if tick%30==0 then timeline:flush();events:flush() end
 if has(gui,"text") then
  local raw,v=sample(0x800D33EC)
  gui.text(10,40,"Bond v1.3 "..phase.." | EC="..raw.." | "..tostring(v))
 end
 emu.frameadvance()
end
termination:write(table.concat({sid,frame,reason},","),"\n")
timeline:close();markers:close();events:close();termination:close();discontinuity:close()
print("[bond.v1.3] DONE "..reason.." session="..sid)
