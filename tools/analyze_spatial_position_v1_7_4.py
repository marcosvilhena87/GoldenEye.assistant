"""Spatial Position Confirmation v1.7.4 — fail-closed temporal RAW audit."""
import argparse,csv,re,struct,math
from pathlib import Path
OFFSETS=("0x05FCB4","0x05FCD4","0x0D61C4","0x0E79C4",
         "0x1F1E88","0x1F1E8C","0x1F1E90","0x2EBCE4")
ACTIONS=("REST_BASELINE","MOVE_LEFT","REST_AFTER_LEFT","MOVE_RIGHT",
         "REST_AFTER_RIGHT","MOVE_FORWARD","REST_AFTER_FORWARD","MOVE_BACK",
         "REST_AFTER_BACK","ROTATE_ONLY","REST_AFTER_ROTATION")
FIELDS=("session","action","offset_hex","start_sample","end_sample","samples",
        "raw_changes","unique_raw","first_raw","last_raw","raw_returned",
        "float_be_first","float_be_last","float_be_delta","float_be_steps_up",
        "float_be_steps_down","float_be_steps_equal","float_be_nonfinite",
        "float_le_first","float_le_last","float_le_delta","float_le_steps_up",
        "float_le_steps_down","float_le_steps_equal","float_le_nonfinite",
        "status")
def read(path):
 with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def dec(raw,end):
 try:
  x=struct.unpack((">" if end=="be" else "<")+"f",bytes.fromhex(raw))[0]
  return x if math.isfinite(x) else None
 except (ValueError,struct.error):return None
def stats(vals,end):
 f=[dec(x,end) for x in vals]
 valid=[(x,y) for x,y in zip(f,f[1:]) if x is not None and y is not None]
 return dict(first=f[0],last=f[-1],
  delta=f[-1]-f[0] if f[0] is not None and f[-1] is not None else None,
  up=sum(y>x for x,y in valid),down=sum(y<x for x,y in valid),
  equal=sum(y==x for x,y in valid),nonfinite=sum(x is None for x in f))
def audit(markers,timeline,termination,discontinuities,sid):
 if discontinuities:raise ValueError("discontinuous session")
 if len(termination)!=1 or termination[0].get("session")!=sid or termination[0].get("reason") not in ("stop","frame_limit") or termination[0].get("active_action")!="NONE":
  raise ValueError("session not cleanly terminated")
 if not markers or not timeline:raise ValueError("missing markers or timeline")
 intervals=[];active=None;last=0
 for marker in markers:
  if marker.get("session")!=sid:raise ValueError("marker session mismatch")
  idx=int(marker["sample_index"])
  if idx<=last:raise ValueError("non-monotonic markers")
  last=idx;label=marker["label"]
  if label=="STOP":
   if active:raise ValueError("STOP inside phase")
   continue
  phase,_,action=label.partition("_")
  if action not in ACTIONS or marker.get("action")!=action or marker.get("phase")!=phase:
   raise ValueError("invalid marker")
  if phase=="BEGIN" and active is None:active=(action,idx,int(marker["frame"]))
  elif phase=="END" and active and active[0]==action and idx>active[1]:
   intervals.append((action,active[1],idx,active[2],int(marker["frame"])))
   active=None
  else:raise ValueError("unmatched marker")
 if active or not intervals:raise ValueError("incomplete phases")
 series={k:[] for k in OFFSETS}
 for row in timeline:
  if row.get("session")!=sid or row.get("offset_hex") not in series:
   raise ValueError("unexpected session/offset")
  raw=row["raw_hex"]
  if not re.fullmatch(r"[0-9A-Fa-f]{8}",raw):raise ValueError("bad raw value")
  series[row["offset_hex"]].append((int(row["sample_index"]),int(row["frame"]),row["action"],raw.upper()))
 size=len(next(iter(series.values())))
 if not size:raise ValueError("empty series")
 for seq in series.values():
  if len(seq)!=size:raise ValueError("missing offset samples")
  for i,(index,frame,action,raw) in enumerate(seq):
   if index!=i+1:raise ValueError("sample gap")
   if i and frame!=seq[i-1][1]+1:raise ValueError("frame gap")
  # keep intervals in sync with the collector's active phase on every frame
 for action,start,end,start_frame,end_frame in intervals:
  for seq in series.values():
   if end>len(seq) or seq[start-1][1]!=start_frame or seq[end-1][1]!=end_frame:
    raise ValueError("marker/frame mismatch")
   if any(seq[i-1][2]!=action for i in range(start-1,end-1)):
    # END sample belongs to NONE; BEGIN..END-1 belongs to the action
    raise ValueError("timeline action mismatch")
   if seq[end-1][2]!="NONE":raise ValueError("phase end not marked inactive")
 rows=[]
 for action,start,end,_,_ in intervals:
  for off,seq in series.items():
   vals=[entry[3] for entry in seq[start-1:end]]
   be=stats(vals,"be");le=stats(vals,"le")
   out=dict(session=sid,action=action,offset_hex=off,start_sample=start,
      end_sample=end,samples=len(vals),raw_changes=sum(x!=y for x,y in zip(vals,vals[1:])),
      unique_raw=len(set(vals)),first_raw=vals[0],last_raw=vals[-1],
      raw_returned=vals[0]==vals[-1],status="raw_probe_not_confirmed_position")
   for endian,s in (("be",be),("le",le)):
    for field,key in (("first","first"),("last","last"),("delta","delta"),
       ("steps_up","up"),("steps_down","down"),("steps_equal","equal"),
       ("nonfinite","nonfinite")):
     out[f"float_{endian}_{field}"]=s[key]
   rows.append(out)
 return rows
def run(sid,root):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid SID")
 stem=root/"output/csv"/f"spatial_v1_7_4_{sid}"
 rows=audit(read(Path(str(stem)+"_markers.csv")),
            read(Path(str(stem)+"_timeline.csv")),
            read(Path(str(stem)+"_termination.csv")),
            read(Path(str(stem)+"_discontinuities.csv")),sid)
 target=Path(str(stem)+"_temporal_audit.csv")
 with target.open("x",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
 return target,rows
def main():
 p=argparse.ArgumentParser();p.add_argument("session")
 p.add_argument("--root",type=Path,default=Path("."))
 a=p.parse_args()
 target,rows=run(a.session,a.root.resolve())
 print(f"Wrote {target} rows={len(rows)}")
 print("RAW temporal association only; no Bond position semantics established.")
if __name__=="__main__":main()
