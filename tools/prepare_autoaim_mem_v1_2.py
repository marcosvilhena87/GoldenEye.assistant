"""Produce an audited, local-only watchlist from the v1.1/v1 intersection."""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"output/csv/autoaim_mem_v1_1_candidates_20261023T045912Z_104773.csv"
def prepare(source=DEFAULT,output=None):
 source=Path(source)
 if not source.is_file():raise ValueError("Missing v1.1 candidate CSV: "+str(source))
 with source.open(encoding="utf-8-sig",newline="") as f:
  rows=list(csv.DictReader(f))
 if not rows:raise ValueError("Empty candidate CSV")
 needed={"session","domain","offset_hex","on_byte","off_byte","in_v1_candidates","status"}
 if not needed.issubset(rows[0]):raise ValueError("Unsupported v1.1 CSV columns")
 filtered=[r for r in rows if r["in_v1_candidates"]=="yes"]
 if not filtered:raise ValueError("No intersecting candidates: run v1.1 analysis --previous-v1-csv first")
 sessions={r["session"] for r in filtered};domains={r["domain"] for r in filtered}
 if len(sessions)!=1 or len(domains)!=1:raise ValueError("Mixed sessions or memory domains")
 offsets=[]
 for r in filtered:
  if r["status"]!="candidate_control_filtered_only":raise ValueError("Unexpected status")
  offset=int(r["offset_hex"],16)
  if not 0<=offset<8388608:raise ValueError("Out-of-range offset")
  on,off=int(r["on_byte"]),int(r["off_byte"])
  if not all(0<=v<=255 for v in (on,off)) or on==off:raise ValueError("Invalid ON/OFF byte pair")
  offsets.append((offset,on,off))
 if len(offsets)!=len(set(o for o,_,_ in offsets)):raise ValueError("Duplicate offset")
 if len(offsets)>1024:raise ValueError("Too many offsets; narrow candidates")
 if next(iter(domains))!="RDRAM":raise ValueError("Expected explicitly observed RDRAM domain")
 output=Path(output) if output else ROOT/"output/commands/autoaim_mem_v1_2_watchlist.csv"
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open("w",encoding="ascii",newline="") as f:
  w=csv.writer(f,lineterminator="\n");w.writerow(["offset_hex","on_byte","off_byte"])
  for o,a,b in sorted(offsets):w.writerow([f"0x{o:06X}",a,b])
 digest=hashlib.sha256(output.read_bytes()).hexdigest()
 meta={"source_csv":str(source),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"v1_1_session":next(iter(sessions)),"domain":next(iter(domains)),"size_bytes":8388608,"candidate_count":len(offsets),"watchlist_sha256":digest,"interpretation":"candidate_only_not_validated"}
 (output.parent/(output.stem+".json")).write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
 print("Watchlist:",output,"count:",len(offsets),"sha256:",digest)
 return output,meta
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=DEFAULT);p.add_argument("--output",type=Path)
 a=p.parse_args()
 try:prepare(a.source,a.output)
 except (OSError,ValueError,KeyError) as e:p.exit(1,"ERROR: "+str(e)+"\n")
