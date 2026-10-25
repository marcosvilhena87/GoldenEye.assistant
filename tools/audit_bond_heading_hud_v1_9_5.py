"""Offline integrity and angular-accuracy audit for read-only heading HUD v1.9.5."""
import argparse,csv,json,math,re
from collections import Counter
from pathlib import Path
def audit(sid,root=Path("output/csv")):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid session ID")
 stem=root/f"bond_heading_hud_v1_9_5_{sid}"
 def read(suffix):
  with Path(str(stem)+suffix).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
 samples=read("_samples.csv");events=read("_events.csv");ends=read("_termination.csv")
 if not samples:raise ValueError("empty samples")
 if any(row["session"]!=sid for row in samples+events+ends):raise ValueError("session mismatch")
 frames=[int(r["frame"]) for r in samples]
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 duplicate=len(frames)!=len(set(frames))
 ack=[e for e in events if e["event"]!="STOP"]
 ack_seq=[int(e["seq"]) for e in ack]
 sequence_ok=ack_seq==list(range(1,len(ack_seq)+1))
 event_order_ok=all(int(a["frame"])<int(b["frame"]) for a,b in zip(events,events[1:]))
 terminal=bool(ends and ends[-1]["reason"]=="stop" and any(e["event"]=="STOP" for e in events))
 rows=[]
 for e in ack:
  frame=int(e["frame"])
  after=next((r for r in samples if int(r["frame"])>=frame),None)
  before=next((r for r in reversed(samples) if int(r["frame"])<frame),None)
  if not after:continue
  def n(v):
   try:return float(v) if v not in ("",None) else None
   except ValueError:return None
  rows.append({"event":e["event"],"frame":frame,"seq":int(e["seq"]),
   "measurement_frame":int(after["frame"]),"valid":after["valid"]=="1",
   "angle_deg":n(after["angle_deg"]),"relative_deg":n(after["relative_deg"]),
   "target_deg":n(after["target_deg"]),"error_deg":n(after["error_deg"]),
   "cumulative_deg":n(after["cumulative_deg"]),
   "cumulative_remaining_deg":n(after["cumulative_remaining_deg"]),
   "previous_cumulative_deg":n(before["cumulative_deg"]) if before else None})
 intervals=[]
 targets=[e for e in events if e["event"].startswith("TARGET_")]
 for i,e in enumerate(targets):
  start=int(e["frame"]);end=int(targets[i+1]["frame"]) if i+1<len(targets) else int(events[-1]["frame"]) if events else frames[-1]+1
  seq=[r for r in samples if start<=int(r["frame"])<end and r["valid"]=="1"]
  if not seq:continue
  def n(v):return float(v) if v else None
  errors=[abs(n(r["error_deg"])) for r in seq if r["error_deg"]]
  intervals.append({"target_command":e["event"],"start_frame":start,"end_frame_exclusive":end,
    "valid_frames":len(seq),"min_absolute_modulo_error_deg":min(errors) if errors else None,
    "last_modulo_error_deg":n(seq[-1]["error_deg"]),
    "last_cumulative_deg":n(seq[-1]["cumulative_deg"]),
    "last_cumulative_remaining_deg":n(seq[-1]["cumulative_remaining_deg"]),
    "reset_reasons":dict(Counter(r["reset_reason"] for r in seq if r["reset_reason"]))})
 valid=sum(r["valid"]=="1" for r in samples)
 return {"protocol":"bond_heading_hud_v1_9_5","session":sid,"samples":len(samples),
  "valid_frames":valid,"invalid_frames":len(samples)-valid,"gaps":gaps,
  "duplicate_frames":duplicate,"acks":len(ack),"ack_sequence_ok":sequence_ok,
  "event_order_ok":event_order_ok,"complete":terminal and not gaps and not duplicate and sequence_ok and event_order_ok,
  "end_reason":ends[-1]["reason"] if ends else None,"command_checkpoints":rows,"target_intervals":intervals,
  "reset_counts":dict(Counter(r["reset_reason"] for r in samples if r["reset_reason"])),
  "physical_heading_validated":False,
  "limitations":["A target command only changes HUD state; it does not attest a performed rotation.",
   "Minimum within-target error is not a sustained settled heading.",
   "360° targets require the cumulative remaining metric; shortest modulo error cannot count turns.",
   "A fixed visual landmark and independent camera/body controls are still required."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("sid");p.add_argument("--root",type=Path,default=Path("output/csv"))
 a=p.parse_args();result=audit(a.sid,a.root)
 dest=a.root/f"bond_heading_hud_v1_9_5_{a.sid}_audit.json"
 if dest.exists():raise FileExistsError(dest)
 dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("HUD v1.9.5 audit",dest,"samples",result["samples"],"complete",result["complete"])
if __name__=="__main__":main()
