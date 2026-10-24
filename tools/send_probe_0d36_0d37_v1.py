"""Create a single read-only probe phase marker; verify 'marked' in Lua."""
import argparse
from pathlib import Path
LABELS={"BASELINE","FORWARD","STOP_MOVE","ROTATE","STOP_ROTATE","BACK",
        "NO_TARGET","TARGET_VISIBLE","AUTOAIM_ON","AUTOAIM_OFF",
        "WEAPON_CHANGE","STOP"}
def send(label,root=Path(".")):
    if label not in LABELS:raise ValueError("Invalid marker")
    root=Path(root)
    sid=(root/"output/sessions/probe_0d36_0d37_session.txt").read_text(
        encoding="utf-8").strip()
    if not sid or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_" for c in sid):
        raise ValueError("Bad session ID")
    prefix="probe_0d36_0d37_"+sid
    folder=root/"output/commands"
    folder.mkdir(parents=True,exist_ok=True)
    marker=root/"output/csv"/(prefix+"_markers.csv")
    if not marker.exists():raise FileNotFoundError("Live markers file missing")
    # Count requests, including unprocessed; never reuse an index.
    index=1
    while (folder/f"{prefix}_{index:04d}.txt").exists():index+=1
    name=folder/f"{prefix}_{index:04d}.txt"
    with name.open("x",encoding="ascii",newline="\n") as fp:
        fp.write(f"SESSION:{sid}\nLABEL:{label}\n")
    return name
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("label",choices=sorted(LABELS))
    ap.add_argument("--root",type=Path,default=Path("."))
    args=ap.parse_args()
    print("Request created:",send(args.label,args.root))
    print("Wait for Lua 'marked' before executing the manual intervention.")
