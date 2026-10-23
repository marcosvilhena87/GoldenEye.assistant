"""Queue one memory snapshot request for the active matching session."""
from pathlib import Path
import sys,uuid,os
root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2 or sys.argv[1] not in ("A1","B","A2"):
    sys.exit("Usage: python tools/send_autoaim_mem_v1.py A1|B|A2")
session_file=root/"output/sessions/autoaim_mem_v1_session.txt"
if not session_file.is_file():sys.exit("No session. Open autoaim_memory_discovery_v1.lua and configure domain.")
session=session_file.read_text(encoding="utf-8").strip()
file=root/"output/commands/autoaim_mem_v1_request.txt"
file.parent.mkdir(parents=True,exist_ok=True)
tmp=file.with_suffix("."+uuid.uuid4().hex+".part")
try:
    tmp.write_text("SESSION:"+session+"\nSNAPSHOT:"+sys.argv[1]+"\n",encoding="utf-8")
    os.replace(tmp,file)
finally:
    tmp.unlink(missing_ok=True)
print("Request submitted:",sys.argv[1],session,"(confirm capture in BizHawk log/manifest)")
