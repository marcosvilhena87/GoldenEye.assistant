"""Conservative byte-wise spatial contrast; results are candidates, not angles."""
import argparse,csv,re
from pathlib import Path
LABELS=("ON_NO_TARGET","ON_LEFT","ON_CENTER","ON_RIGHT","OFF_LEFT","OFF_CENTER","OFF_RIGHT","ON_LEFT_REPEAT")
def analyze(data):
 size=len(data[LABELS[0]])
 if size!=8388608 or any(len(data[k])!=size for k in LABELS):raise ValueError("Size mismatch")
 out=[]
 a=data["ON_LEFT"];b=data["ON_CENTER"];c=data["ON_RIGHT"];d=data["OFF_LEFT"];e=data["OFF_CENTER"];f=data["OFF_RIGHT"];repeat=data["ON_LEFT_REPEAT"];no=data["ON_NO_TARGET"]
 # Candidate selection deliberately conservative, no presumed numeric format, endian or angular units.
 for i in range(size):
  if a[i]!=repeat[i]:continue
  if len({a[i],b[i],c[i]})<3:continue
  if not (d[i]==e[i]==f[i]):continue
  out.append(dict(offset_hex=f"0x{i:06X}",on_left=a[i],on_center=b[i],on_right=c[i],
                  off_constant=d[i],on_no_target=no[i],repeated_on_left=repeat[i],
                  status="spatial_byte_candidate_only"))
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--directory",default="output");a=p.parse_args()
 if not re.fullmatch(r"[A-Za-z0-9_]+",a.session):p.error("Bad session ID")
 root=Path(a.directory);manifest=root/"csv"/f"horizontal_v1_manifest_{a.session}.csv"
 with manifest.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
 if len(rows)!=8 or [r["label"] for r in rows]!=list(LABELS) or any(r["session"]!=a.session or r["domain"]!="RDRAM" or int(r["size"])!=8388608 for r in rows):raise ValueError("Incomplete/invalid manifest")
 data={}
 for r in rows:
  # use derived expected paths; never trust arbitrary paths in manifest
  path=root/"archive"/f"horizontal_v1_{a.session}_{r['label']}.bin"
  data[r["label"]]=path.read_bytes()
 out=analyze(data)
 dest=root/"csv"/f"horizontal_v1_candidates_{a.session}.csv"
 with dest.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=("offset_hex","on_left","on_center","on_right","off_constant","on_no_target","repeated_on_left","status"))
  w.writeheader();w.writerows(out)
 print("Wrote",dest,"candidates",len(out))
 print("No angular interpretation, memory writes, or validated symbols.")
if __name__=="__main__":main()
