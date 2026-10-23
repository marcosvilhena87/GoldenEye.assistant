"""Send single-use command files; no concurrent open append to BizHawk files."""
from pathlib import Path
import os
import sys
import uuid

QUEUE = Path("manual_controls_v2_2_inbox")
def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python tools/send_controls_v22.py PHASE gameplay | OBSERVED 1 fire_manual | RESULT 1 yes | NOTE text")
    kind=sys.argv[1].upper()
    values=sys.argv[2:]
    if kind in {"OBSERVED","RESULT"}:
        if len(values)!=2 or not values[0].isdigit():
            raise SystemExit(f"{kind} requires trial_id and value")
        payload=kind+":"+values[0]+":"+values[1]
    elif kind in {"PHASE","NOTE"}:
        payload=kind+":"+" ".join(values)
    else:
        raise SystemExit("Unsupported command: "+kind)
    QUEUE.mkdir(exist_ok=True)
    existing=[int(f.stem) for f in QUEUE.glob("*.cmd") if f.stem.isdigit()]
    number=max(existing,default=0)+1
    while (QUEUE/f"{number:06d}.cmd").exists():
        number+=1
    destination=QUEUE/f"{number:06d}.cmd"
    temp=QUEUE/("_tmp_"+uuid.uuid4().hex+".part")
    try:
        temp.write_text(payload+"\n",encoding="ascii")
        os.replace(temp,destination)
    finally:
        temp.unlink(missing_ok=True)
    print(f"Enqueued #{number}: {payload}")
if __name__=="__main__":
    main()
