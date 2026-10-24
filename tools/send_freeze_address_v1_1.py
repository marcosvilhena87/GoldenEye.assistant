"""Send STOP to a running Freeze Address Mapping v1.1 session."""
import argparse
from pathlib import Path
def stop(root=Path(".")):
    sid=(root/"output/sessions/freeze_address_v1_1_session.txt").read_text(encoding="utf-8").strip()
    if not sid or any(c not in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_" for c in sid):
        raise ValueError("Invalid session identifier")
    stem="freeze_address_v1_1_"+sid
    if not (root/"output/csv"/(stem+"_timeline.csv")).exists():
        raise FileNotFoundError("Session timeline missing")
    path=root/"output/commands"/(stem+"_STOP.txt")
    with path.open("x",encoding="ascii",newline="\n") as f:f.write("STOP:"+sid+"\n")
    return path
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("command",choices=["STOP"]);a=p.parse_args()
    print("STOP requested:",stop())
