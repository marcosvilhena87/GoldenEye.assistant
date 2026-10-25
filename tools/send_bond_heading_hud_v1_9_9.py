"""Send HUD commands one at a time; wait for ACK in Lua console."""
import argparse,os,tempfile
from pathlib import Path
COMMANDS={"BASELINE_STILL","CAMERA_PITCH_UP","HOLD_CAMERA_UP","CAMERA_PITCH_DOWN","HOLD_CAMERA_DOWN","AIM_MODE_PITCH_UP","HOLD_AIM_UP","AIM_MODE_PITCH_DOWN","HOLD_AIM_DOWN","AIM_MODE_YAW_LEFT","HOLD_AIM_LEFT","AIM_MODE_YAW_RIGHT","HOLD_AIM_RIGHT","BODY_TURN_LEFT","HOLD_BODY_LEFT","BODY_TURN_RIGHT","HOLD_BODY_RIGHT","STRAFE_LEFT","HOLD_STRAFE_LEFT","STRAFE_RIGHT","HOLD_STRAFE_RIGHT","AUTOAIM_STATIC","HOLD_AUTOAIM_STATIC","AUTOAIM_MOVING","HOLD_AUTOAIM_MOVING","WEAPON_CHANGE","HOLD_WEAPON","REFERENCE","TARGET_0","TARGET_90","TARGET_180","TARGET_270","TARGET_360","STOP"}
def send(command,root=None):
 if command not in COMMANDS:raise ValueError("invalid command")
 root=Path(root) if root else Path(__file__).resolve().parent.parent/"output"
 sid=(root/"sessions/bond_heading_hud_v1_9_9_session.txt").read_text(encoding="ascii").strip()
 if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
 commands=root/"commands";commands.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=commands,prefix=".heading_hud_",suffix=".tmp")
 tmp=Path(name)
 try:
  with os.fdopen(fd,"w",encoding="ascii",newline="\n") as f:f.write(command+"\n");f.flush();os.fsync(f.fileno())
  for i in range(1,10000):
   dest=commands/f"bond_heading_hud_v1_9_9_{sid}_{i:04d}.txt"
   if dest.exists():continue
   os.rename(tmp,dest);return dest
  raise RuntimeError("command sequence exhausted")
 finally:
  if tmp.exists():tmp.unlink()
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("command",choices=sorted(COMMANDS));a=p.parse_args()
 print("Created",send(a.command),"; await ACK in Lua console")
