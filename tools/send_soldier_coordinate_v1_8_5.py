"""Atomically publish read-only Soldier Coordinate v1.8.5 commands."""
import argparse
import os
import tempfile
from pathlib import Path
LABELS = {"BASELINE","BOND_ROTATE","BOND_MOVE","SOLDIER_MOVE","SOLDIER_FREEZE","NEW_SAVE","STOP"}
def send(label, root=None):
    if label not in LABELS:raise ValueError("invalid label")
    root=Path(root) if root else Path(__file__).resolve().parent.parent/"output"
    sid=(root/"sessions/soldier_coordinate_v1_8_5_session.txt").read_text().strip()
    if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
    directory=root/"commands";directory.mkdir(parents=True,exist_ok=True)
    fd,temp_path=tempfile.mkstemp(prefix=".soldier_v185_",suffix=".tmp",dir=directory)
    temp=Path(temp_path)
    try:
        with os.fdopen(fd,"w",encoding="ascii",newline="\n") as f:
            f.write("LABEL:"+label+"\n");f.flush();os.fsync(f.fileno())
        for n in range(1,10000):
            target=directory/f"soldier_coordinate_v1_8_5_{sid}_{n:04d}.txt"
            try:
                os.rename(temp,target)
                return target
            except FileExistsError:continue
        raise RuntimeError("command count exceeded")
    finally:
        if temp.exists():temp.unlink()
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("label",choices=sorted(LABELS))
    p.add_argument("--root",type=Path)
    a=p.parse_args()
    print("Created",send(a.label,a.root),"; await CAPTURED confirmation")
