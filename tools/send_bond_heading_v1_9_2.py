"""Atomically send operator labels to v1.9.2 read-only collector."""
import argparse, os, tempfile
from pathlib import Path
LABELS={"BASELINE_STILL","TURN_LEFT_90","HOLD_90","TURN_LEFT_180","HOLD_180","TURN_LEFT_270","HOLD_270","TURN_LEFT_360","HOLD_360","TURN_RIGHT_270","HOLD_R270","TURN_RIGHT_180","HOLD_R180","TURN_RIGHT_90","HOLD_R90","TURN_RIGHT_0","HOLD_ORIGIN","MOVE_FORWARD","HOLD_MOVE","STOP"}
def send(label,root=None):
    if label not in LABELS:raise ValueError("invalid label")
    root=Path(root) if root is not None else Path(__file__).resolve().parent.parent/"output"
    sid=(root/"sessions/bond_heading_v1_9_2_session.txt").read_text(encoding="ascii").strip()
    if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
    commands=root/"commands";commands.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=commands,prefix=".spatial_v186_",suffix=".tmp")
    tmp=Path(name)
    try:
        with os.fdopen(fd,"w",encoding="ascii",newline="\n") as f:
            f.write("LABEL:"+label+"\n");f.flush();os.fsync(f.fileno())
        for i in range(1,10000):
            path=commands/f"bond_heading_v1_9_2_{sid}_{i:04d}.txt"
            if path.exists():continue
            try:os.rename(tmp,path);return path
            except FileExistsError:continue
        raise RuntimeError("too many commands")
    finally:
        if tmp.exists():tmp.unlink()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("label",choices=sorted(LABELS));a=p.parse_args()
    print("Created",send(a.label),"; await MARKED before next command")
