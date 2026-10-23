"""Send phase annotations for read-only analog logging via atomic session queue."""
from pathlib import Path
import sys,uuid,os
P="analog_v1"
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"output"
def main():
    if len(sys.argv)<3 or sys.argv[1].upper() not in ("PHASE","NOTE"):
        raise SystemExit("Usage: python tools/send_analog_v1.py PHASE neutral|up|down|left|right|up_left|up_right|down_left|down_right")
    session=(OUTPUT/"sessions"/(P+"_session.txt")).read_text(encoding="utf-8").strip()
    folder=(OUTPUT/"commands"/(P+"_inbox"))/session
    folder.mkdir(parents=True,exist_ok=True)
    ids=[int(p.stem) for p in folder.glob("*.cmd") if p.stem.isdigit()]
    n=max(ids,default=0)+1
    dest=folder/f"{n:06d}.cmd"
    tmp=folder/("_tmp_"+uuid.uuid4().hex+".part")
    command=sys.argv[1].upper()+":"+" ".join(sys.argv[2:])
    try:
        tmp.write_text("SESSION:"+session+"\n"+command+"\n",encoding="utf-8")
        os.replace(tmp,dest)
    finally:
        tmp.unlink(missing_ok=True)
    print("Queued",n,command,"session",session)
if __name__=="__main__":
    main()
