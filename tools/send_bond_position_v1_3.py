"""Bond v1.3 safe operator phase sender."""
from pathlib import Path
import sys
VALID={"BASELINE","TARGET_EC","TARGET_F4","WRITE_PRE","WRITE_APPLIED","WRITE_OBSERVE","STOP"}
def send(label,root=Path("output")):
    if label not in VALID: raise ValueError("Invalid label: "+label)
    sid=(root/"sessions/bond_position_v1_3_session.txt").read_text().strip()
    if not sid or any(c in sid for c in "/\\\r\n"): raise ValueError("Invalid SID")
    directory=root/"commands";directory.mkdir(parents=True,exist_ok=True)
    for seq in range(1,10000):
        p=directory/f"bond_position_v1_3_{sid}_{seq:04d}.txt"
        if not p.exists():
            with p.open("x",encoding="ascii",newline="\n") as f:
                f.write(f"SESSION:{sid}\nLABEL:{label}\n")
            return p
    raise RuntimeError("Too many commands")
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: python -m tools.send_bond_position_v1_3 LABEL")
    print("Created",send(sys.argv[1]),"; await MARKED confirmation")
