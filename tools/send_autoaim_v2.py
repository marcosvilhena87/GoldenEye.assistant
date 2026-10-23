"""Queue session-safe annotations for the Auto-Aim v2 observer."""
from pathlib import Path
import os,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
P="autoaim_v2"
def main():
    if len(sys.argv)<3 or sys.argv[1].upper() not in ("PHASE","EVENT","NOTE"):
        raise SystemExit("Usage: python tools/send_autoaim_v2.py PHASE|EVENT|NOTE text")
    session_file=ROOT/"output"/"sessions"/(P+"_session.txt")
    if not session_file.is_file():
        raise SystemExit("Session absent. Start autoaim_mapping_v2.lua in BizHawk.")
    sid=session_file.read_text(encoding="utf-8").strip()
    inbox=ROOT/"output"/"commands"/(P+"_inbox")/sid
    inbox.mkdir(parents=True,exist_ok=True)
    ids=[int(p.stem) for p in inbox.glob("*.cmd") if p.stem.isdigit()]
    n=max(ids,default=0)+1
    dest=inbox/f"{n:06d}.cmd"
    temp=inbox/("_tmp_"+uuid.uuid4().hex+".part")
    cmd=sys.argv[1].upper()+":"+" ".join(sys.argv[2:])
    try:
        temp.write_text("SESSION:"+sid+"\n"+cmd+"\n",encoding="utf-8")
        os.replace(temp,dest)
    finally:
        temp.unlink(missing_ok=True)
    print("Queued",n,cmd,"session",sid)
if __name__=="__main__":
    main()
