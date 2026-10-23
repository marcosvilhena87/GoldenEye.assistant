"""Atomic command writer for Auto-Aim Mapping v3."""
from pathlib import Path
import sys, os, uuid
ROOT=Path(__file__).resolve().parents[1]
PREFIX="autoaim_v3_1"
def main():
    if len(sys.argv)<3 or sys.argv[1].upper() not in ("PHASE","EVENT","NOTE","INTERVENTION","INITIAL"):
        raise SystemExit("Usage: python tools/send_autoaim_v3_1.py PHASE|EVENT|NOTE|INTERVENTION|INITIAL value")
    session_path=ROOT/"output/sessions/autoaim_v3_1_session.txt"
    if not session_path.exists():
        raise SystemExit("No session file: start autoaim_mapping_v3.lua in BizHawk")
    session=session_path.read_text(encoding="utf-8").strip()
    inbox=ROOT/"output/commands/autoaim_v3_1_inbox"/session
    inbox.mkdir(parents=True,exist_ok=True)
    occupied=[int(f.stem) for f in inbox.glob("*.cmd") if f.stem.isdigit()]
    index=max(occupied,default=0)+1
    final=inbox/f"{index:06d}.cmd"
    temp=inbox/("_tmp_"+uuid.uuid4().hex+".part")
    command=sys.argv[1].upper()+":"+" ".join(sys.argv[2:])
    try:
        temp.write_text(f"SESSION:{session}\n{command}\n",encoding="utf-8")
        os.replace(temp,final)
    finally:
        temp.unlink(missing_ok=True)
    print(f"Queued {index} {command} session {session}")
if __name__=="__main__":
    main()
