"""Analyze strictly matched A1/B/A2 raw memory dumps: potential reversible bytes only."""
import csv, pathlib, sys
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=ROOT/"output/csv/autoaim_mem_v1_manifest.csv"
if not manifest.exists(): sys.exit("No manifest; collect A1, B, A2 in BizHawk first")
with manifest.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
sid=sys.argv[1] if len(sys.argv)>1 else (rows[-1]["session"] if rows else "")
items={r["label"]:r for r in rows if r["session"]==sid}
if set(("A1","B","A2"))-items.keys(): sys.exit("Missing one or more of A1/B/A2 in session "+sid)
selected=[items[x] for x in ("A1","B","A2")]
if len({(r["domain"],r["size"]) for r in selected})!=1:sys.exit("Domain/size mismatch")
def path(p):
    obj=pathlib.Path(p)
    resolved=(ROOT/obj).resolve()
    if not resolved.is_relative_to(ROOT.resolve()):sys.exit("Unsafe dump path")
    return resolved
data=[path(r["path"]).read_bytes() for r in selected]
length=int(selected[0]["size"])
if any(len(blob)!=length for blob in data):sys.exit("Dump size mismatch")
reversible=[(i,a,b) for i,(a,b,a2) in enumerate(zip(*data)) if a==a2 and a!=b]
changed=sum(x!=y for x,y in zip(data[0],data[1]))
out=ROOT/"output/csv"/("autoaim_mem_v1_candidates_"+sid+".csv")
with out.open("w",encoding="utf-8",newline="") as f:
    writer=csv.writer(f);writer.writerow(["session","domain","offset_hex","a1_byte","b_byte","a2_byte","status"])
    for i,a,b in reversible:
        writer.writerow([sid,selected[0]["domain"],f"0x{i:06X}",a,b,a,"candidate_reversible_byte_only"])
print("Session:",sid,"domain:",selected[0]["domain"],"bytes:",length)
print("A1/B changed bytes:",changed,"A1==A2 and !=B:",len(reversible))
print("CSV:",out)
print("WARNING: correlated offsets can represent UI state, gameplay changes or noise, not proven auto-aim.")
