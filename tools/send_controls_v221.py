"""Session-bound command sender for GoldenEye 2.2.1; Python 3.8+."""
from pathlib import Path
import csv
import os
import sys
import uuid

PREFIX = "manual_controls_v2_2_1"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
SESSION_FILE = OUTPUT / "sessions" / (PREFIX + "_session.txt")
INBOX = OUTPUT / "commands" / (PREFIX + "_inbox")
PENDING = OUTPUT / "csv" / (PREFIX + "_pending.csv")

def current_session():
    if not SESSION_FILE.exists():
        raise SystemExit("Detector v2.2.1 not started (session manifest missing)")
    value = SESSION_FILE.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("Empty session manifest")
    return value

def main():
    if len(sys.argv)<3:
        raise SystemExit("Usage: python tools/send_controls_v221.py PHASE gameplay | OBSERVED Z latest fire_manual | RESULT Z latest yes | LIST")
    kind = sys.argv[1].upper()
    session = current_session()
    args = sys.argv[2:]
    if kind == "LIST":
        rows = []
        if PENDING.exists():
            with PENDING.open(newline="", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f) if r.get("session")==session]
        for r in rows:
            print(f"#{r['trial_id']} {r['control']} {r['expected_action']} frame={r['press_frame']} phase={r['phase']}")
        if not rows:
            print("No pending trials for", session)
        return
    if kind in ("OBSERVED","RESULT"):
        if len(args)!=3:
            raise SystemExit(f"Usage: {kind} BUTTON trial_id|latest value")
        button, selector, value=args
        if not PENDING.exists():
            raise SystemExit("Pending trials report not found")
        with PENDING.open(newline="",encoding="utf-8") as f:
            rows=[r for r in csv.DictReader(f) if r.get("session")==session and r.get("control")==button]
        if selector.lower()=="latest":
            if not rows:
                raise SystemExit("No pending trial for "+button)
            selected=max(rows,key=lambda x:int(x["trial_id"]))
        else:
            matches=[r for r in rows if r["trial_id"]==selector]
            if not matches:
                raise SystemExit(f"Trial {selector} for {button} not pending in current session")
            selected=matches[0]
        if kind=="RESULT" and value not in ("yes","no","unknown"):
            raise SystemExit("RESULT must be yes|no|unknown")
        if kind=="OBSERVED" and value=="":
            raise SystemExit("OBSERVED value cannot be empty")
        payload=f"{kind}:{selected['trial_id']}:{button}:{value}"
    elif kind in ("PHASE","NOTE"):
        if not args:
            raise SystemExit(f"{kind} requires value")
        payload=kind+":"+" ".join(args)
    else:
        raise SystemExit("Unsupported command: "+kind)
    destination_dir=INBOX/session
    destination_dir.mkdir(parents=True,exist_ok=True)
    numbers=[int(x.stem) for x in destination_dir.glob("*.cmd") if x.stem.isdigit()]
    n=max(numbers,default=0)+1
    dest=destination_dir/f"{n:06d}.cmd"
    if dest.exists():
        raise SystemExit("Command collision")
    tmp=destination_dir/("_tmp_"+uuid.uuid4().hex+".part")
    try:
        tmp.write_text("SESSION:"+session+"\n"+payload+"\n",encoding="utf-8")
        os.replace(tmp,dest)
    finally:
        tmp.unlink(missing_ok=True)
    if current_session()!=session:
        raise SystemExit("Session changed while sending; command safely isolated from the new session")
    print(f"Session {session} | queued #{n}: {payload}")

if __name__=="__main__":
    main()
