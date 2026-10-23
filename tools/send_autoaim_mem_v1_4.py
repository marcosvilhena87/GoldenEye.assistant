"""Create numbered immutable atomic v1.4 operator markers."""
from pathlib import Path
import argparse, os, re
ROOT=Path(__file__).resolve().parents[1]
LABELS={"BASE_ON","BASE_OFF","ON_AGAIN","MENU_OPEN","MENU_CLOSED","OTHER_OPTION_CHANGED","NO_TARGET","TARGET_VISIBLE","WEAPON_CHANGE","LEVEL_RESTART","STOP"}
def send(label,root=ROOT):
    if label not in LABELS:raise ValueError("Unknown marker")
    session=(root/"output/sessions/autoaim_mem_v1_4_session.txt").read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+",session):raise ValueError("Invalid session")
    directory=root/"output/commands"
    existing=sorted(directory.glob(f"autoaim_mem_v1_4_{session}_????.txt"))
    seq=len(existing)+1
    for i,item in enumerate(existing,1):
        if item.name!=f"autoaim_mem_v1_4_{session}_{i:04d}.txt":
            raise ValueError("Command sequence gap")
    dest=directory/f"autoaim_mem_v1_4_{session}_{seq:04d}.txt"
    pending=dest.with_suffix(".txt.pending")
    body=f"SESSION:{session}\nLABEL:{label}\n"
    with pending.open("x",encoding="ascii",newline="\n") as f:
        f.write(body);f.flush();os.fsync(f.fileno())
    try:
        if dest.exists():raise FileExistsError(dest)
        os.replace(pending,dest)
    finally:
        pending.unlink(missing_ok=True)
    return dest
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("label",choices=sorted(LABELS))
    a=p.parse_args()
    print("Request created:",send(a.label).name)
    print("Confirm 'marked' in BizHawk; sender does not change game state.")
