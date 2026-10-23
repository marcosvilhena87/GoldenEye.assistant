"""Atomic marker sender for v1.5, sequential and bracketed."""
import argparse,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIONS=("AUTOAIM_OFF","AUTOAIM_ON","MENU_ONLY","OTHER_OPTION","NO_TARGET","TARGET_VISIBLE","WEAPON_CHANGE","LEVEL_RESTART")
LABELS={"STOP"}|{f"{phase}_{a}" for a in ACTIONS for phase in ("BEGIN","END")}
def send(label,root=ROOT):
    if label not in LABELS:raise ValueError("Unknown label")
    sid=(root/"output/sessions/autoaim_mem_v1_5_session.txt").read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Bad session ID")
    directory=root/"output/commands"
    existing=sorted(directory.glob(f"autoaim_mem_v1_5_{sid}_????.txt"))
    active=None
    for i,path in enumerate(existing,1):
        if path.name!=f"autoaim_mem_v1_5_{sid}_{i:04d}.txt":raise ValueError("Missing sequence number")
        body=path.read_text(encoding="ascii")
        found=re.fullmatch(r"SESSION:"+re.escape(sid)+r"\nLABEL:([A-Z0-9_]+)\n",body)
        if not found:raise ValueError("Malformed prior command")
        marker=found.group(1)
        if marker=="STOP":
            raise ValueError("Session already stopped")
        phase,action=marker.split("_",1)
        if phase=="BEGIN" and active is None:active=action
        elif phase=="END" and active==action:active=None
        else:raise ValueError("Invalid previous marker sequence")
    if label=="STOP":
        if active is not None:raise ValueError("Close active action first")
    else:
        phase,action=label.split("_",1)
        if (phase=="BEGIN" and active is not None) or (phase=="END" and active!=action):
            raise ValueError("Bracket violation; active="+str(active))
    seq=len(existing)+1
    dest=directory/f"autoaim_mem_v1_5_{sid}_{seq:04d}.txt"
    temp=dest.with_suffix(".txt.pending")
    try:
        with temp.open("x",encoding="ascii",newline="\n") as f:
            f.write(f"SESSION:{sid}\nLABEL:{label}\n");f.flush();os.fsync(f.fileno())
        if dest.exists():raise FileExistsError(dest)
        os.replace(temp,dest)
    finally:temp.unlink(missing_ok=True)
    return dest
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("label",choices=sorted(LABELS));args=p.parse_args()
    print("Request created:",send(args.label).name)
    print("Wait for the exact Lua 'marked' confirmation before performing the action / sending END.")
