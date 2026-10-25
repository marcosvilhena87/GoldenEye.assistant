"""Send HUD commands one at a time; wait for ACK in Lua console."""
import argparse,os,tempfile
from pathlib import Path
COMMANDS={"BASELINE_STILL","C_LEFT","HOLD_C_LEFT","C_RIGHT","HOLD_C_RIGHT","C_UP","HOLD_C_UP","C_DOWN","HOLD_C_DOWN","R_STICK_LEFT","HOLD_R_LEFT","R_STICK_RIGHT","HOLD_R_RIGHT","R_STICK_UP","HOLD_R_UP","R_STICK_DOWN","HOLD_R_DOWN","AUTOAIM_TARGET","HOLD_AUTOAIM","WEAPON_CHANGE","HOLD_WEAPON","MOVE_FORWARD_NO_TURN","HOLD_MOVE","LANDMARK_MATCH","HOLD_LANDMARK","REFERENCE","TARGET_0","TARGET_90","TARGET_180","TARGET_270","TARGET_360","STOP"}
def send(command,root=None):
 if command not in COMMANDS:raise ValueError("invalid command")
 root=Path(root) if root else Path(__file__).resolve().parent.parent/"output"
 sid=(root/"sessions/bond_heading_hud_v1_9_7_session.txt").read_text(encoding="ascii").strip()
 if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
 commands=root/"commands";commands.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=commands,prefix=".heading_hud_",suffix=".tmp")
 tmp=Path(name)
 try:
  with os.fdopen(fd,"w",encoding="ascii",newline="\n") as f:f.write(command+"\n");f.flush();os.fsync(f.fileno())
  for i in range(1,10000):
   dest=commands/f"bond_heading_hud_v1_9_7_{sid}_{i:04d}.txt"
   if dest.exists():continue
   os.rename(tmp,dest);return dest
  raise RuntimeError("command sequence exhausted")
 finally:
  if tmp.exists():tmp.unlink()
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("command",choices=sorted(COMMANDS));a=p.parse_args()
 print("Created",send(a.command),"; await ACK in Lua console")
