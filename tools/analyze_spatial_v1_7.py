"""Spatial v1.7: ranked float32 BE/LE candidates, not validated positions."""
import argparse,csv,math,re,struct
from pathlib import Path

FIELDS=("offset_hex","endianness","baseline","moved","rotation",
        "movement_delta","rotation_delta","return_error",
        "movement_magnitude","status")

def read(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def decode(buf,offset,endianness):
 x=struct.unpack_from((">" if endianness=="big" else "<")+"f",buf,offset)[0]
 return x if math.isfinite(x) else None

def rank_snapshots(baseline,moved,rotation,returned=None,limit=100):
 if not(len(baseline)==len(moved)==len(rotation)) or (returned is not None and len(returned)!=len(baseline)):
  raise ValueError("Snapshot lengths mismatch")
 out=[]
 for endian in ("big","little"):
  for i in range(0,len(baseline)-3,4):
   if baseline[i:i+4]==moved[i:i+4]:continue
   a=decode(baseline,i,endian);b=decode(moved,i,endian);c=decode(rotation,i,endian)
   if any(x is None or abs(x)>1e6 for x in (a,b,c)):continue
   diff=b-a
   if not (0.00001<abs(diff)<100000):continue
   turn=c-a
   # Rotation may change nearby or unrelated fields; prioritize those that do not.
   if abs(turn)>max(0.001,abs(diff)*0.05):continue
   ret=decode(returned,i,endian) if returned is not None else None
   ret_err=abs(ret-a) if ret is not None else None
   if returned is not None and (ret_err is None or ret_err>max(0.001,abs(diff)*0.1)):continue
   out.append(dict(offset_hex=f"0x{i:06X}",endianness=endian,baseline=a,moved=b,rotation=c,
     movement_delta=diff,rotation_delta=turn,return_error=ret_err,
     movement_magnitude=abs(diff),status="candidate_not_validated_position"))
 out.sort(key=lambda r:(abs(r["rotation_delta"])/(abs(r["movement_delta"])+1e-9),
                      r["return_error"] if r["return_error"] is not None else 0,
                      -r["movement_magnitude"],r["offset_hex"]))
 return out[:limit]

def validate_manifest(rows,markers,termination,discontinuities,sid,root):
 if discontinuities:raise ValueError("timeline discontinuity: refuse session")
 if len(termination)!=1 or termination[0].get("session")!=sid or termination[0].get("reason") not in ("stop","frame_limit") or termination[0].get("pending_label")!="NONE":
  raise ValueError("session not cleanly terminated")
 if not rows or not markers:raise ValueError("missing snapshots/markers")
 last=0;mapping={}
 for row in rows:
  if row["session"]!=sid:raise ValueError("session mismatch")
  sample=int(row["sample_index"])
  if sample<=last:raise ValueError("non-monotonic snapshots")
  last=sample
  label=row["label"]
  if label in mapping:raise ValueError("duplicate snapshot label: "+label)
  relative=Path(row["path"])
  if relative.is_absolute() or ".." in relative.parts or len(relative.parts)!=3 or relative.parts[:2]!=("output","archive"):
   raise ValueError("invalid snapshot path")
  full=root/relative
  if not full.is_file() or full.stat().st_size!=8388608 or int(row["size_bytes"])!=8388608:
   raise ValueError("snapshot missing or invalid size")
  mapping[label]=full
 matched={(x["sample_index"],x["frame"],x["label"]) for x in markers if x["label"]!="STOP"}
 if matched!={(x["sample_index"],x["frame"],x["label"]) for x in rows}:
  raise ValueError("snapshot/marker mismatch")
 if any(markers[i]["session"]!=sid or int(markers[i]["sample_index"])<=int(markers[i-1]["sample_index"]) for i in range(1,len(markers))):
  raise ValueError("invalid marker ordering")
 return mapping

def run(sid,root,base_label,movement_label,rotation_label,return_label=None,limit=100):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid session")
 stem=root/"output/csv"/("spatial_v1_7_"+sid)
 rows=read(Path(str(stem)+"_snapshots.csv"))
 mapping=validate_manifest(rows,read(Path(str(stem)+"_markers.csv")),
    read(Path(str(stem)+"_termination.csv")),read(Path(str(stem)+"_discontinuities.csv")),sid,root)
 names=[base_label,movement_label,rotation_label]+([return_label] if return_label else [])
 if any(name not in mapping for name in names):raise ValueError("requested label not captured")
 data=[mapping[name].read_bytes() for name in names]
 found=rank_snapshots(data[0],data[1],data[2],data[3] if return_label else None,limit)
 target=Path(str(stem)+"_bond_position_candidates.csv")
 with target.open("x",newline="",encoding="utf-8") as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(found)
 return target,found

def main():
 p=argparse.ArgumentParser()
 p.add_argument("session")
 p.add_argument("--baseline",default="BOND_BASELINE")
 p.add_argument("--movement",default="BOND_MOVE_LEFT")
 p.add_argument("--rotation",default="BOND_ROTATE_LEFT")
 p.add_argument("--return-label",default=None)
 p.add_argument("--limit",type=int,default=100)
 p.add_argument("--root",type=Path,default=Path("."))
 a=p.parse_args()
 if not 1<=a.limit<=1000:p.error("--limit must be 1..1000")
 path,rows=run(a.session,a.root,a.baseline,a.movement,a.rotation,a.return_label,a.limit)
 print(f"Wrote {path} candidates={len(rows)}")
 print("These are candidate fields, NOT Bond positions. Soldier identification and nearest-target association are not yet validated.")
if __name__=="__main__":main()
