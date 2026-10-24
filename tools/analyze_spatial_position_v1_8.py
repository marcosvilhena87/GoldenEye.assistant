"""Spatial Position Discovery v1.8 — scan full 8 MiB across independent movement axes.

Operator-labeled snapshots; labels do not prove game inputs. Read-only, finite
float32 big/little hypotheses, no assumed address, no validated X/Y/Z.
"""
import argparse,csv,math,mmap,re,struct
from pathlib import Path
from contextlib import ExitStack
try:
 from tools.analyze_spatial_v1_7 import read,validate_manifest
except ModuleNotFoundError:
 from analyze_spatial_v1_7 import read,validate_manifest
LABELS=("BASELINE_STILL","LEFT_MID","LEFT_END","LEFT_HOLD",
        "RIGHT_MID","RIGHT_END","RIGHT_HOLD",
        "FORWARD_MID","FORWARD_END","FORWARD_HOLD",
        "BACK_MID","BACK_END","BACK_HOLD","ROTATE_END")
FIELDS=("offset_hex","endianness","baseline","left_mid","left_end","left_hold",
        "right_mid","right_end","right_hold","forward_mid","forward_end","forward_hold",
        "back_mid","back_end","back_hold","rotate_end",
        "left_delta","right_delta","forward_delta","back_delta",
        "left_progressive","right_progressive","forward_progressive","back_progressive",
        "left_hold_error","right_hold_error","forward_hold_error","back_hold_error",
        "rotation_error","lateral_opposite","longitudinal_opposite",
        "independent_axes","classification","candidate_only")
SIZE=8388608

def value(buf,pos,end):
 x=struct.unpack_from((">" if end=="big" else "<")+"f",buf,pos)[0]
 return x if math.isfinite(x) and abs(x)<=1e8 else None

def classify(vals,min_delta=0.01,hold_ratio=.05,rotate_ratio=.05):
 if len(vals)!=14 or any(x is None for x in vals):return None
 (base,lm,le,lh,rm,re,rh,fm,fe,fh,bm,be,bh,rot)=vals
 movement=((base,lm,le,lh),(lh,rm,re,rh),(rh,fm,fe,fh),(fh,bm,be,bh))
 results=[]
 for start,mid,end,hold in movement:
  delta=end-start
  threshold=max(min_delta,abs(delta)*.05)
  progress=abs(mid-start)>min_delta*.2 and abs(end-mid)>min_delta*.2 and (mid-start)*(end-mid)>0
  stable=abs(hold-end)<=max(min_delta*.25,abs(delta)*hold_ratio)
  results.append((delta,progress,stable,abs(hold-end)))
 dl,dr,df,db=[r[0] for r in results]
 lateral=(dl*dr<0 and min(abs(dl),abs(dr))>=min_delta)
 longit=(df*db<0 and min(abs(df),abs(db))>=min_delta)
 lateral_ok=lateral and all(r[1] and r[2] for r in results[:2])
 forward_ok=longit and all(r[1] and r[2] for r in results[2:])
 axis=lateral_ok and forward_ok
 max_move=max(abs(x) for x in (dl,dr,df,db))
 stable_rot=abs(rot-bh)<=max(min_delta*.25,max_move*rotate_ratio)
 if not stable_rot or not (lateral_ok or forward_ok):return None
 label="two_axes_unverified" if axis else "lateral_axis_unverified" if lateral_ok else "forward_axis_unverified"
 return dict(zip(("left_delta","right_delta","forward_delta","back_delta"),(dl,dr,df,db)),
  left_progressive=results[0][1],right_progressive=results[1][1],
  forward_progressive=results[2][1],back_progressive=results[3][1],
  left_hold_error=results[0][3],right_hold_error=results[1][3],
  forward_hold_error=results[2][3],back_hold_error=results[3][3],
  rotation_error=abs(rot-bh),lateral_opposite=lateral,
  longitudinal_opposite=longit,independent_axes=axis,
  classification=label,candidate_only=True)

def scan(buffers,min_delta=.01):
 if len(buffers)!=len(LABELS) or any(len(b)!=SIZE for b in buffers):
  raise ValueError("expected fourteen complete 8MiB snapshots")
 found=[]
 for i in range(0,SIZE,4):
  # Movement must change at least one of the raw offsets.
  if buffers[0][i:i+4]==buffers[2][i:i+4] and buffers[3][i:i+4]==buffers[5][i:i+4] and buffers[6][i:i+4]==buffers[8][i:i+4] and buffers[9][i:i+4]==buffers[11][i:i+4]:
   continue
  for end in ("big","little"):
   vals=[value(b,i,end) for b in buffers]
   metrics=classify(vals,min_delta)
   if metrics is None:continue
   entry=dict(offset_hex=f"0x{i:06X}",endianness=end)
   entry.update(zip(("baseline","left_mid","left_end","left_hold",
    "right_mid","right_end","right_hold","forward_mid","forward_end","forward_hold",
    "back_mid","back_end","back_hold","rotate_end"),vals))
   entry.update(metrics);found.append(entry)
 found.sort(key=lambda r:(not r["independent_axes"],r["rotation_error"],r["offset_hex"],r["endianness"]))
 return found

def run(sid,root,min_delta=.01):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("Invalid SID")
 stem=root/"output"/"csv"/("spatial_v1_8_"+sid)
 def part(suffix):return read(Path(str(stem)+suffix))
 mapping=validate_manifest(part("_snapshots.csv"),part("_markers.csv"),
  part("_termination.csv"),part("_discontinuities.csv"),sid,root)
 if list(mapping)!=list(LABELS) or len(mapping)!=len(LABELS):
  raise ValueError("All 14 snapshots required in canonical order")
 path=Path(str(stem)+"_coordinate_candidates.csv")
 if path.exists():raise FileExistsError("Refusing overwrite")
 with ExitStack() as stack:
  mm=[]
  for label in LABELS:
   fh=stack.enter_context(mapping[label].open("rb"))
   mm.append(stack.enter_context(mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ)))
  rows=scan(mm,min_delta)
 with path.open("x",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
 return path,rows

def main():
 p=argparse.ArgumentParser();p.add_argument("session")
 p.add_argument("--root",type=Path,default=Path("."))
 p.add_argument("--min-delta",type=float,default=.01)
 a=p.parse_args()
 if not math.isfinite(a.min_delta) or a.min_delta<=0:p.error("min-delta must be positive finite")
 path,rows=run(a.session,a.root.resolve(),a.min_delta)
 print(f"Wrote {path} candidates={len(rows)}")
 print("Heuristics assume operator-verified movement, not measured input. No validated positions.")
if __name__=="__main__":main()
