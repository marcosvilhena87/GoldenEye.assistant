"""Send one sequential ON/OFF marker to the running BizHawk read-only probe."""
import argparse
from pathlib import Path
LABELS={"OFF1","ON1","OFF2","ON2","STOP"}
def send(label,root=Path(".")):
    if label not in LABELS: raise ValueError("Invalid label")
    root=Path(root)
    sid=(root/"output/sessions/freeze_address_v1_session.txt").read_text(encoding="utf8").strip()
    if not sid or any(not (c.isalnum() or c=="_") for c in sid):
        raise ValueError("Invalid session id")
    stem="freeze_address_v1_"+sid
    marker=root/"output/csv"/(stem+"_markers.csv")
    if not marker.exists(): raise FileNotFoundError("Running session markers missing")
    folder=root/"output/commands"
    folder.mkdir(parents=True,exist_ok=True)
    n=1
    while (folder/f"{stem}_{n:04d}.txt").exists(): n+=1
    path=folder/f"{stem}_{n:04d}.txt"
    with path.open("x",encoding="ascii",newline="\n") as out:
        out.write(f"SESSION:{sid}\nLABEL:{label}\n")
    return path
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("label",choices=sorted(LABELS))
    args=p.parse_args()
    print("Marker created:",send(args.label))
    print("Wait until Lua reports marked before changing phase.")
