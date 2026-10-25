"""v1.8.7 freeze timing and pair identity audit. No world-coordinate claims."""
import argparse,csv,json
from collections import defaultdict,Counter
from pathlib import Path
WATCH=[(0x06A120,0x20F578),(0x06A124,0x20F57C),(0x06A128,0x20F580),(0x06A154,0x20F728),(0x06A158,0x20F72C),(0x06A15C,0x20F730),(0x06D254,0x0D33E8)]
CORE=[0x20F594,0x20F5AC,0x20F580,0x06A128]
def load(path):
 with open(path,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def analyze(sid,root=Path("output/csv"),quiet_frames=120):
 if not sid or any(c in sid for c in "/\\\r\n") or ".." in sid:raise ValueError("invalid session")
 if quiet_frames<1:raise ValueError("invalid quiet window")
 stem=root/("soldier_identity_v1_8_7_"+sid)
 rows=load(str(stem)+"_timeline.csv");marks=load(str(stem)+"_markers.csv");ends=load(str(stem)+"_termination.csv")
 if not rows:raise ValueError("empty timeline")
 timeline=defaultdict(dict);phase={}
 for row in rows:
  if row["session"]!=sid:raise ValueError("mixed sessions")
  n=int(row["frame"]);o=int(row["offset_hex"],16)
  if o in timeline[n]:raise ValueError("duplicate sample")
  timeline[n][o]=row["raw_be"]
  if n in phase and phase[n]!=row["phase"]:raise ValueError("mixed phases")
  phase[n]=row["phase"]
 frames=sorted(timeline);fields=set(timeline[frames[0]])
 missing=[n for n in frames if set(timeline[n])!=fields]
 if missing:raise ValueError("incomplete frames")
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 changes={o:[] for o in fields}
 for prev,cur in zip(frames,frames[1:]):
  if cur!=prev+1:continue
  for o in fields:
   if timeline[prev][o]!=timeline[cur][o]:changes[o].append(cur)
 markerlist=[{"frame":int(m["frame"]),"label":m["label"]} for m in marks]
 request=[m for m in markerlist if m["label"]=="FREEZE_REQUEST_ON"]
 end_frame=frames[-1]
 episodes=[]
 for m in request:
  start=m["frame"];next_mark=next((x for x in markerlist if x["frame"]>start and x["label"] in ("FREEZE_REQUEST_OFF","SOLDIER_RESTARTED","STOP","FREEZE_REQUEST_ON")),None)
  stop=min(next_mark["frame"]-1 if next_mark else end_frame,end_frame)
  item={"request_frame":start,"phase_end":stop,"fields":{}}
  for o in CORE:
   events=[n for n in changes.get(o,[]) if start<=n<=stop]
   last=events[-1] if events else None
   first=(last+1 if last is not None else start)
   available=first+quiet_frames-1<=stop and all(n in timeline for n in range(first,first+quiet_frames))
   item["fields"][f"0x{o:06X}"]={"changes_after_request":len(events),"last_change_frame":last,
    "first_possible_quiet_frame":first,"delay_frames":first-start,"quiet_window_observed":available}
  episodes.append(item)
 pairs=[]
 for a,b in WATCH:
  if a not in fields or b not in fields:continue
  unequal=[n for n in frames if timeline[n][a]!=timeline[n][b]]
  phases=Counter(phase[n] for n in unequal)
  pairs.append({"a":f"0x{a:06X}","b":f"0x{b:06X}","equal_fraction":1-len(unequal)/len(frames),"unequal_by_phase":dict(phases)})
 return {"protocol":"soldier_identity_freeze_v1_8_7","session":sid,"frames":len(frames),
  "capture_complete":bool(ends and ends[-1]["reason"]=="stop" and not gaps),
  "gaps":gaps,"markers":markerlist,"freeze_episodes":episodes,"duplicate_pairs":pairs,
  "changes_by_phase":[{"offset_hex":f"0x{o:06X}","total_changes":len(ev),"phases":dict(Counter(phase[n] for n in ev))} for o,ev in sorted(changes.items())],
  "soldier_identity_validated":False,"xyz_validated":False,"cross_save_validated":False,
  "limitations":["Operator confirmation is not independent RAM identity evidence.",
  "Quiet-window estimate is retrospective: last change, not proven first physical freeze.",
  "Offset comparisons valid only for this individual session; repeat in a different save."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));p.add_argument("--quiet-frames",type=int,default=120);a=p.parse_args()
 result=analyze(a.session,a.root,a.quiet_frames)
 path=a.root/f"soldier_identity_v1_8_7_{a.session}_analysis.json"
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Soldier identity v1.8.7",path,"frames",result["frames"],"complete",result["capture_complete"])
if __name__=="__main__":main()
