"""Stop the active read-only enemy snapshot probe; never send ON/OFF commands."""
from pathlib import Path
import argparse
def stop(root=Path(".")):
 sid=(root/"output/sessions/enemy_freeze_v1_session.txt").read_text(encoding="utf-8").strip()
 if not sid or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for c in sid):
  raise ValueError("Invalid session id")
 stem="enemy_freeze_v1_"+sid
 if not (root/"output/csv"/(stem+"_events.csv")).exists():raise FileNotFoundError("Active session events not found")
 out=root/"output/commands"/(stem+"_STOP.txt")
 with out.open("x",encoding="ascii",newline="\n") as f:f.write("STOP:"+sid+"\n")
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("command",choices=["STOP"]);p.parse_args()
 print("STOP requested:",stop())
