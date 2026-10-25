"""Create sequential, immutable, operator markers; no memory writes."""
import pathlib,sys
LABELS={"BASELINE","BEGIN_FORWARD","END_FORWARD","BEGIN_BACK","END_BACK","BEGIN_LEFT","END_LEFT","BEGIN_RIGHT","END_RIGHT","BEGIN_ROTATE","END_ROTATE","WRITE_PRE","WRITE_APPLIED","WRITE_OBSERVE","STOP"}
if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in LABELS:
        raise SystemExit("Use python tools/send_bond_position_v1_2.py LABEL. Labels: "+", ".join(sorted(LABELS)))
    root=pathlib.Path("output")
    sid=(root/"sessions/bond_position_v1_2_session.txt").read_text().strip()
    if not sid or "/" in sid or "\\" in sid: raise SystemExit("Bad session")
    d=root/"commands";d.mkdir(parents=True,exist_ok=True)
    for n in range(1,10000):
        path=d/f"bond_position_v1_2_{sid}_{n:04d}.txt"
        if not path.exists():
            with path.open("x",encoding="ascii",newline="\n") as fp:
                fp.write(f"SESSION:{sid}\nLABEL:{sys.argv[1]}\n")
            print("Created",path,"; wait for MARKED before next action")
            break
