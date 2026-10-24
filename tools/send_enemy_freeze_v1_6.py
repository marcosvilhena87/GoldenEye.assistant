"""Send CAM or STOP marker to active v1.6 BizHawk Lua session."""
import argparse
from pathlib import Path

def send(command,root=Path(".")):
    if command not in ("CAM","STOP"):raise ValueError("Only CAM or STOP")
    sid=(root/"output/sessions/enemy_freeze_v1_6_session.txt").read_text(encoding="ascii").strip()
    if not sid or any(c not in "0123456789TZ_" for c in sid):
        raise ValueError("Invalid session ID")
    stem="enemy_freeze_v1_6_"+sid
    if not (root/"output/csv"/(stem+"_events.csv")).exists():
        raise FileNotFoundError("Session events missing")
    path=root/"output/commands"/(stem+"_"+command+".txt")
    with path.open("x",encoding="ascii") as f:f.write(command+":"+sid+"\n")
    return path

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("CAM","STOP"))
    args=p.parse_args()
    print("Command created:",send(args.command))
