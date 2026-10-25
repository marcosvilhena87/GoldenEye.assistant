"""Atomically send operator labels to v1.8.10 read-only collector."""
import argparse, os, tempfile
from pathlib import Path
LABELS={"BASELINE","FREEZE_REQUEST_ON","FREEZE_CONFIRMED","FROZEN_BASELINE","BOND_APPROACH","BOND_STOP_NEAR","BOND_ROTATE","BOND_RETREAT","BOND_STOP_FAR","STOP"}
def send(label,root=None):
    if label not in LABELS:raise ValueError("invalid label")
    root=Path(root) if root is not None else Path(__file__).resolve().parent.parent/"output"
    sid=(root/"sessions/soldier_frozen_v1_8_10_session.txt").read_text(encoding="ascii").strip()
    if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
    commands=root/"commands";commands.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=commands,prefix=".spatial_v186_",suffix=".tmp")
    tmp=Path(name)
    try:
        with os.fdopen(fd,"w",encoding="ascii",newline="\n") as f:
            f.write("LABEL:"+label+"\n");f.flush();os.fsync(f.fileno())
        for i in range(1,10000):
            path=commands/f"soldier_frozen_v1_8_10_{sid}_{i:04d}.txt"
            if path.exists():continue
            try:os.rename(tmp,path);return path
            except FileExistsError:continue
        raise RuntimeError("too many commands")
    finally:
        if tmp.exists():tmp.unlink()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("label",choices=sorted(LABELS));a=p.parse_args()
    print("Created",send(a.label),"; await MARKED before next command")
