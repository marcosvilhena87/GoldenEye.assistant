"""v1.8.8.1: observational chase analysis; not controlled axis identification."""
import argparse,csv,json
from pathlib import Path
from collections import defaultdict,Counter
PHASES=("BASELINE","BOND_APPROACH","SOLDIER_CHASE","BOND_RETREAT","SOLDIER_REPOSITION","FREEZE_REQUEST_ON","FREEZE_CONFIRMED")
PAIRS=((0x06A120,0x20F578),(0x06A124,0x20F57C),(0x06A128,0x20F580),(0x06A154,0x20F728),(0x06A158,0x20F72C),(0x06A15C,0x20F730))
TARGETS=(0x20F594,0x20F5AC,0x20F580,0x06A128)
def load(path):
 with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def analyze(sid,root=Path("output/csv"),min_quiet=120):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid SID")
 if min_quiet<1:raise ValueError("invalid quiet window")
 stem=root/("soldier_chase_v1_8_8_1_"+sid)
 rows=load(Path(str(stem)+"_timeline.csv"));marks=load(Path(str(stem)+"_markers.csv"));end=load(Path(str(stem)+"_termination.csv"))
 if not rows:raise ValueError("no samples")
 timeline=defaultdict(dict);phases={}
 for row in rows:
  if row["session"]!=sid:raise ValueError("mixed sessions")
  n=int(row["frame"]);o=int(row["offset_hex"],16)
  if o in timeline[n]:raise ValueError("duplicate sample")
  timeline[n][o]=row["raw_be"]
  if n in phases and phases[n]!=row["phase"]:raise ValueError("mixed phases")
  phases[n]=row["phase"]
 frames=sorted(timeline);fields=set(timeline[frames[0]])
 if any(set(timeline[n])!=fields for n in frames):raise ValueError("incomplete frame")
 gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
 events={o:defaultdict(list) for o in fields}
 for a,b in zip(frames,frames[1:]):
  if b!=a+1:continue
  for o in fields:
   if timeline[a][o]!=timeline[b][o]:events[o][phases[b]].append(b)
 stats=[{"offset_hex":f"0x{o:06X}","changes_by_phase":{p:len(events[o][p]) for p in PHASES},
         "total_changes":sum(len(v) for v in events[o].values())} for o in sorted(fields)]
 pairs=[]
 for a,b in PAIRS:
  if a not in fields or b not in fields:continue
  differences=Counter(phases[n] for n in frames if timeline[n][a]!=timeline[n][b])
  pairs.append({"a":f"0x{a:06X}","b":f"0x{b:06X}","equal_fraction":1-sum(differences.values())/len(frames),"unequal_by_phase":dict(differences)})
 freeze=[int(m["frame"]) for m in marks if m["label"]=="FREEZE_REQUEST_ON"]
 stop=next((int(m["frame"]) for m in marks if m["label"]=="STOP"),frames[-1]+1)
 freeze_results=[]
 for start in freeze:
  finish=min((int(m["frame"]) for m in marks if int(m["frame"])>start and m["label"] in ("STOP","FREEZE_REQUEST_ON")),default=stop)-1
  item={"request_frame":start,"interval_end":finish,"fields":{}}
  for o in TARGETS:
   if o not in fields:continue
   changes=sorted(n for arr in events[o].values() for n in arr if start<=n<=finish)
   last=changes[-1] if changes else None
   candidate=(last+1) if last is not None else start
   item["fields"][f"0x{o:06X}"]={"changes":len(changes),"last_change":last,"quiet_start_candidate":candidate,
     "quiet_window_observed":candidate+min_quiet-1<=finish}
  freeze_results.append(item)
 return {"protocol":"soldier_chase_observation_v1_8_8_1","session":sid,"frames":len(frames),
         "capture_complete":bool(end and end[-1]["reason"]=="stop" and not gaps),
         "gaps":gaps,"markers":marks,"fields":stats,"duplicate_pairs":pairs,"freeze_episodes":freeze_results,
         "controlled_soldier_direction":False,"axes_validated":False,"soldier_identity_validated":False,
         "limitations":["Soldier is not operator-controlled, only observed after Bond stimuli.",
         "Movement of Bond and soldier may overlap; phase labels cannot isolate causation.",
         "No absolute XYZ or pointer/address persistence inferred."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 result=analyze(a.session,a.root)
 out=a.root/f"soldier_chase_v1_8_8_1_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
 print("Soldier chase v1.8.8.1",out,"frames",result["frames"],"complete",result["capture_complete"])
if __name__=="__main__":main()
