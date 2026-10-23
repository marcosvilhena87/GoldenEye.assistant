"""Audit temporal windows and decode raw bytes, without asserting semantics."""
import argparse,csv,math,re,struct
from pathlib import Path
OFFSETS=("0x0D3995","0x0D3D3D")
FIELDNAMES=("session","action","begin_frame","end_frame","offset_hex","samples",
            "distinct_raw","changes","first_raw","last_raw","first_f32_le",
            "last_f32_le","min_f32_le","max_f32_le","status")
def rows_csv(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def f32(raw):
 try:
  number=struct.unpack("<f",bytes.fromhex(raw))[0]
  return number if math.isfinite(number) else None
 except (ValueError,struct.error):raise ValueError("Invalid raw hex "+str(raw))
def analyze(markers,timeline,session):
 stack=None;windows=[]
 for marker in markers:
  label=marker["label"];frame=int(marker["frame"])
  if marker.get("session")!=session:raise ValueError("Different session in markers")
  if label=="STOP":
   if stack is not None:raise ValueError("STOP during action")
   continue
  phase,action=label.split("_",1)
  if phase=="BEGIN":
   if stack is not None:raise ValueError("Nested action")
   stack=(action,frame)
  elif phase=="END":
   if stack is None or stack[0]!=action or frame<=stack[1]:raise ValueError("Unmatched END")
   windows.append((action,stack[1],frame));stack=None
  else:raise ValueError("Invalid phase")
 if stack is not None:raise ValueError("Unclosed action")
 series={o:[] for o in OFFSETS}
 for row in timeline:
  offset=row["offset_hex"]
  if offset not in series or row["session"]!=session or not re.fullmatch(r"[0-9A-Fa-f]{8}",row["raw_hex"]):
   raise ValueError("Invalid timeline record")
  series[offset].append((int(row["frame"]),row["raw_hex"].upper()))
 if not windows:raise ValueError("No completed windows")
 output=[]
 for action,start,end in windows:
  for offset in OFFSETS:
   selected=[(frame,raw) for frame,raw in series[offset] if start<=frame<=end]
   if not selected or selected[0][0]>start or selected[-1][0]<end:
    raise ValueError("Incomplete frame coverage for "+action+" "+offset)
   raw=[r for _,r in selected];nums=[f32(r) for r in raw];finite=[v for v in nums if v is not None]
   output.append(dict(session=session,action=action,begin_frame=start,end_frame=end,
    offset_hex=offset,samples=len(raw),distinct_raw=len(set(raw)),
    changes=sum(x!=y for x,y in zip(raw,raw[1:])),first_raw=raw[0],last_raw=raw[-1],
    first_f32_le=nums[0],last_f32_le=nums[-1],min_f32_le=min(finite) if finite else "",
    max_f32_le=max(finite) if finite else "",status="temporal_candidate_only"))
 return output
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--directory",type=Path,default=Path("output"));a=p.parse_args()
 if not re.fullmatch(r"[A-Za-z0-9_]+",a.session):p.error("Invalid session")
 pre=a.directory/"csv"/f"horizontal_v1_2_{a.session}"
 out=analyze(rows_csv(Path(str(pre)+"_markers.csv")),rows_csv(Path(str(pre)+"_timeline.csv")),a.session)
 dest=Path(str(pre)+"_windows.csv")
 with dest.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDNAMES);w.writeheader();w.writerows(out)
 print("Wrote",dest,"window rows",len(out),"without validating field semantics")
if __name__=="__main__":main()
