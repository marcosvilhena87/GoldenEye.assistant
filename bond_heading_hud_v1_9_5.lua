-- Bond heading v1.9.5 live calibration HUD, RDRAM READ ONLY.
-- Experimental vector: X=0x0D33F8 Y=0x0D3400; not physically calibrated.
local D="RDRAM"
assert(memory and memory.read_u8 and memory.getmemorydomainsize and emu and emu.frameadvance and emu.framecount and gui and gui.text,"BizHawk memory/GUI API unavailable")
assert(memory.getmemorydomainsize(D)==8388608,"Expected 8 MiB RDRAM")
local X,Y=0x0D33F8,0x0D3400
local ref=nil
local prev=nil
local total=0
local turns=0
local target=90
local seq=1
local sid=os.date("!%Y%m%dT%H%M%SZ").."_"..emu.framecount()
local prefix="output/commands/bond_heading_hud_v1_9_5_"..sid.."_"
local pointer=assert(io.open("output/sessions/bond_heading_hud_v1_9_5_session.txt","wb"))
pointer:write(sid,"\n");pointer:close()
local stem="output/csv/bond_heading_hud_v1_9_5_"..sid
local function fresh(path,header)
 local test=io.open(path,"rb")
 assert(not test,"Output exists: "..path)
 local f=assert(io.open(path,"wb"))
 f:write(header,"\n");f:flush()
 return f
end
local samples=fresh(stem.."_samples.csv","session,frame,command_seq,target_deg,x_raw,y_raw,x,y,norm_squared,valid,angle_deg,reference_deg,relative_deg,error_deg,cumulative_deg,cumulative_remaining_deg,step_deg,reset_reason")
local events=fresh(stem.."_events.csv","session,frame,seq,event,target_deg,reference_deg,cumulative_deg")
local termination=fresh(stem.."_termination.csv","session,frame,reason")
local function csvnum(v) if v==nil then return "" end return string.format("%.12g",v) end
local function raw32(o)
 local a,b,c,d=memory.read_u8(o,D),memory.read_u8(o+1,D),memory.read_u8(o+2,D),memory.read_u8(o+3,D)
 return a*16777216+b*65536+c*256+d
end
local function float32(o)
 local u=raw32(o)
 local sign=(u>=2147483648) and -1 or 1
 local exponent=math.floor(u/8388608)%256
 local mantissa=u%8388608
 if exponent==255 then return nil end
 if exponent==0 then return sign*(mantissa/8388608)*2^(-126) end
 return sign*(1+mantissa/8388608)*2^(exponent-127)
end
-- Portable atan2 for NLua/Lua runtimes without math.atan2.
local function atan2_compat(y,x)
 if x>0 then return math.atan(y/x) end
 if x<0 and y>=0 then return math.atan(y/x)+math.pi end
 if x<0 and y<0 then return math.atan(y/x)-math.pi end
 if x==0 and y>0 then return math.pi/2 end
 if x==0 and y<0 then return -math.pi/2 end
 return nil -- undefined at origin
end
local function principal(deg) return ((deg+180)%360)-180 end
local function poll()
 local path=string.format("%s%04d.txt",prefix,seq)
 local f=io.open(path,"rb")
 if not f then return false end
 local msg=f:read("*a");f:close()
 local cmd=msg:gsub("^%s+",""):gsub("%s+$","")
 local ok=false
 if cmd=="REFERENCE" then ref=nil;prev=nil;total=0;turns=0;ok=true
 elseif cmd=="TARGET_0" then target=0;ok=true
 elseif cmd=="TARGET_90" then target=90;ok=true
 elseif cmd=="TARGET_180" then target=180;ok=true
 elseif cmd=="TARGET_270" then target=270;ok=true
 elseif cmd=="TARGET_360" then target=360;ok=true
 elseif cmd=="STOP" then events:write(string.format("%s,%d,%d,STOP,%d,%s,%s\n",sid,emu.framecount(),seq,target,csvnum(ref),csvnum(total)));events:flush();termination:write(string.format("%s,%d,stop\n",sid,emu.framecount()));termination:close();events:close();samples:close();print("[bond.heading.hud.v1.9.5] STOPPED");return true
 end
 if not ok then error("Unrecognized HUD command: "..cmd) end
 events:write(string.format("%s,%d,%d,%s,%d,%s,%s\n",sid,emu.framecount(),seq,cmd,target,csvnum(ref),csvnum(total)));events:flush()
 print("[bond.heading.hud.v1.9.5] ACK "..cmd.." frame="..emu.framecount())
 seq=seq+1
 return false
end
print("[bond.heading.hud.v1.9.5] SESSION "..sid.." READ ONLY")
while true do
 if poll() then break end
 local rawx,rawy=raw32(X),raw32(Y)\n local x,y=float32(X),float32(Y)
 local valid=x and y and x==x and y==y and math.abs(x*x+y*y-1)<0.02
 local angle=nil
 if valid then local rad=atan2_compat(y,x); if rad then angle=math.deg(rad) else valid=false end end
 local step=nil\n local reset_reason=""\n if not valid then prev=nil;reset_reason="invalid_vector" end
 if valid and angle then
  if not ref then ref=angle;total=0;prev=angle
  elseif prev then
   local delta=principal(angle-prev)\n   step=delta
   if math.abs(delta)<90 then total=total+delta else print("[bond.heading.hud.v1.9.5] WARNING large angular jump: "..delta);total=0;ref=angle;reset_reason="large_jump";step=nil end
   prev=angle
  end
 end
 local rel=valid and principal(angle-ref) or nil
 local targetDeg=target==360 and 0 or target
 local err=rel and principal(targetDeg-rel) or nil
 local cumulative_remaining=valid and (target-total) or nil
 local norm=x and y and x*x+y*y or nil
 samples:write(table.concat({sid,emu.framecount(),seq-1,target,string.format("%08X",rawx),string.format("%08X",rawy),csvnum(x),csvnum(y),csvnum(norm),valid and "1" or "0",csvnum(angle),csvnum(ref),csvnum(rel),csvnum(err),csvnum(total),csvnum(cumulative_remaining),csvnum(step),reset_reason},",").."\n")\n if emu.framecount()%30==0 then samples:flush() end\n gui.text(8,18,"Bond Heading HUD v1.9.5 (EXPERIMENTAL)")
 gui.text(8,32,string.format("Vector: %s",valid and "VALID" or "INVALID"))
 gui.text(8,46,string.format("X: %s   Y: %s",x and string.format("%.6f",x) or "?",y and string.format("%.6f",y) or "?"))
 gui.text(8,60,string.format("x^2+y^2: %s",norm and string.format("%.9f",norm) or "?"))
 gui.text(8,74,string.format("atan2 angle: %s",angle and string.format("%.2f deg",angle) or "?"))
 gui.text(8,88,string.format("reference: %s",ref and string.format("%.2f deg",ref) or "?"))
 gui.text(8,102,string.format("relative: %s",rel and string.format("%.2f deg",rel) or "?"))
 gui.text(8,116,string.format("target: %d deg; error: %s",target,err and string.format("%.2f deg",err) or "?"))
 gui.text(8,130,string.format("cumulative: %.2f deg (%.2f turns)",total,total/360))
 gui.text(8,158,string.format("target cumulative %d: remaining %s",target,cumulative_remaining and string.format("%.2f deg",cumulative_remaining) or "?"))
 gui.text(8,144,"REFERENCE to reset; no controller or RAM writes")
 emu.frameadvance()
end
