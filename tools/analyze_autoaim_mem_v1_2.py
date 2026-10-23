"""Score candidate stability against manual on/off and no-change controls."""
from pathlib import Path
import csv,argparse
ROOT=Path(__file__).resolve().parents[1]
LABELS=("ON1","ON_STABLE","OFF1","OFF_STABLE","ON2","MENU_NO_CHANGE","OFF2","ON3")
ON=("ON1","ON_STABLE","ON2","MENU_NO_CHANGE","ON3")
OFF=("OFF1","OFF_STABLE","OFF2")
def analyze(session=None,root=ROOT):
 manifest=root/"output/csv/autoaim_mem_v1_2_manifest.csv"
 with manifest.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
 sid=session or rows[-1]["session"]
 entries=[r for r in rows if r["session"]==sid]
 if [r["label"] for r in entries]!=list(LABELS):raise ValueError("Incomplete/out-of-order manifest")
 count=int(entries[0]["count"])
 if count<1 or len({(r["domain"],r["count"]) for r in entries})!=1:raise ValueError("Domain/count mismatch")
 path=root/"output/csv/autoaim_mem_v1_2_samples.csv"
 readings={}
 with path.open(encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["session"]!=sid:continue
   key=row["offset_hex"]
   if row["label"] not in LABELS:raise ValueError("Unexpected label")
   if row["domain"]!=entries[0]["domain"]:raise ValueError("Domain mismatch")
   group=readings.setdefault(key,{})
   if row["label"] in group:raise ValueError("Duplicated candidate sample")
   group[row["label"]]=int(row["byte"])
 if len(readings)!=count:raise ValueError("Missing candidate rows")
 out=root/"output/csv"/f"autoaim_mem_v1_2_validation_{sid}.csv"
 results={"consistent":0,"inconsistent":0}
 with out.open("w",newline="",encoding="utf-8") as f:
  w=csv.writer(f);w.writerow(["session","domain","offset_hex","on_byte","off_byte","status"])
  for offset,values in sorted(readings.items()):
   if set(values)!=set(LABELS):raise ValueError("Incomplete sample at "+offset)
   on={values[x] for x in ON};off={values[x] for x in OFF}
   strict=len(on)==1 and len(off)==1 and next(iter(on))!=next(iter(off))
   results["consistent" if strict else "inconsistent"]+=1
   w.writerow([sid,entries[0]["domain"],offset,next(iter(on)) if len(on)==1 else "",next(iter(off)) if len(off)==1 else "",
               "candidate_repeated_controls_only" if strict else "failed_candidate_controls"])
 print("Session:",sid,"tested:",len(readings),"consistent:",results["consistent"],"inconsistent:",results["inconsistent"])
 print("CSV:",out)
 print("No memory symbol validated; require verified ROM/core, fresh restart and controls.")
 return results
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--session");a=p.parse_args()
 try:analyze(a.session)
 except (OSError,ValueError,KeyError,IndexError) as e:p.exit(1,"ERROR: "+str(e)+"\n")
