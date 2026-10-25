#!/usr/bin/env python3
"""Send a single phase marker to Bond Position v1.1; never writes game memory."""
import pathlib, sys
LABELS={"BASELINE","FORWARD","HOLD_F","BACK","HOLD_B","STRAFE_LEFT","STRAFE_RIGHT","ROTATE","HOLD_ROT","WRITE_BEFORE","WRITE_AFTER","WRITE_HOLD1","WRITE_HOLD30","WRITE_HOLD120","RESTORE","STOP"}
def main():
    if len(sys.argv)!=2 or sys.argv[1] not in LABELS:
        raise SystemExit("Usage: python tools/send_bond_position_v1_1.py LABEL; valid: "+", ".join(sorted(LABELS)))
    root=pathlib.Path("output")
    sid=(root/"sessions/bond_position_v1_1_session.txt").read_text(encoding="utf-8").strip()
    if not sid or "/" in sid or "\\" in sid: raise SystemExit("Invalid session ID")
    directory=root/"commands"
    directory.mkdir(parents=True,exist_ok=True)
    stem="bond_position_v1_1_"+sid
    for n in range(1,9999):
        path=directory/f"{stem}_{n:04d}.txt"
        if not path.exists():
            # exclusively create; rerun only after collector reports MARKED
            with path.open("x",encoding="ascii",newline="\n") as f:
                f.write(f"SESSION:{sid}\nLABEL:{sys.argv[1]}\n")
            print("Created",path,"; verify MARKED in BizHawk before next action")
            return
    raise SystemExit("Command capacity reached")
if __name__=="__main__": main()
