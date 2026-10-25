"""v1.8.15: event-conditioned alias update ordering; offline v1.8.13 CSV."""
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path
A=(0x06D248,0x06D250)
B=(0x0D33EC,0x0D33F4)
def audit(sid,root=Path("output/csv")):
 if not sid or ".." in sid or any(c in sid for c in "/\\\r\n"):raise ValueError("invalid SID")
 path=Path(root)/f"bond_position_v1_8_13_{sid}_timeline.csv"
 frames=defaultdict(dict);phases={}
 with path.open(newline="",encoding="utf-8") as f:
  reader=csv.DictReader(f)
  if not {"session","frame","phase","offset_hex","raw_be"}.issubset(reader.fieldnames or []):raise ValueError("invalid header")
  for row in reader:
   if row["session"]!=sid:raise ValueError("foreign session")
   n=int(row["frame"]);o=int(row["offset_hex"],16)
   if o in frames[n]:raise ValueError("duplicate frame/offset")
   if n in phases and phases[n]!=row["phase"]:raise ValueError("mixed phase")
   frames[n][o]=row["raw_be"];phases[n]=row["phase"]
 if not frames:raise ValueError("empty timeline")
 order=sorted(frames)
 valid=[n for n in order if all(o in frames[n] for o in (*A,*B))]
 def pair(n,offsets):
  return tuple(frames[n][o] for o in offsets)
 def status(n):
  av=pair(n,A);bv=pair(n,B)
  mismatched=av!=bv
  prior=frames.get(n-1);following=frames.get(n+1)
  direct_prev=bool(prior and all(o in prior for o in (*A,*B)))
  direct_next=bool(following and all(o in following for o in (*A,*B)))
  # At divergence, determine if one current vector equals the other region's
  # adjacent snapshot. A match is diagnostic, not causal proof.
  a_leads=b_leads=False
  labels=[]
  if direct_prev:
   if av==pair(n-1,B):labels.append("A_matches_previous_B")
   if bv==pair(n-1,A):labels.append("B_matches_previous_A")
  if direct_next:
   if av==pair(n+1,B):labels.append("A_matches_next_B")
   if bv==pair(n+1,A):labels.append("B_matches_next_A")
  if direct_prev and av!=pair(n-1,A) and bv==pair(n-1,B):a_leads=True
  if direct_prev and bv!=pair(n-1,B) and av==pair(n-1,A):b_leads=True
  if direct_next:
   if a_leads and av==pair(n+1,B):labels.append("A_leads_B_one_frame")
   if b_leads and bv==pair(n+1,A):labels.append("B_leads_A_one_frame")
  return labels
 mismatches=[]
 for n in valid:
  if pair(n,A)==pair(n,B):continue
  before=frames.get(n-1,{})
  after=frames.get(n+1,{})
  prev_ready=all(o in before for o in (*A,*B))
  next_ready=all(o in after for o in (*A,*B))
  a=pair(n,A);b=pair(n,B)
  interpretations=status(n)
  if prev_ready:
   a_changed=a!=pair(n-1,A);b_changed=b!=pair(n-1,B)
  else:a_changed=b_changed=None
  recovered=next_ready and pair(n+1,A)==pair(n+1,B)
  mismatches.append({"frame":n,"phase":phases[n],"a_raw":list(a),"b_raw":list(b),
    "a_changed_from_previous":a_changed,"b_changed_from_previous":b_changed,
    "matched_adjacent":interpretations,"resynchronized_next_frame":recovered,
    "one_frame_ordering":"A_first" if "A_leads_B_one_frame" in interpretations else
      "B_first" if "B_leads_A_one_frame" in interpretations else "not_demonstrated"})
 changed_events=[]
 for n in valid:
  if n-1 not in frames or not all(o in frames[n-1] for o in (*A,*B)):continue
  ac=pair(n,A)!=pair(n-1,A);bc=pair(n,B)!=pair(n-1,B)
  if ac or bc:
   changed_events.append({"frame":n,"phase":phases[n],"a_changed":ac,
                          "b_changed":bc,"same_frame_equal":pair(n,A)==pair(n,B)})
 phase_summary={}
 for p in sorted(set(phases.values())):
  ev=[e for e in changed_events if e["phase"]==p]
  mm=[m for m in mismatches if m["phase"]==p]
  phase_summary[p]={"change_events":len(ev),"both_updated":sum(e["a_changed"] and e["b_changed"] for e in ev),
    "only_a_updated":sum(e["a_changed"] and not e["b_changed"] for e in ev),
    "only_b_updated":sum(e["b_changed"] and not e["a_changed"] for e in ev),
    "divergences":len(mm)}
 orderings=Counter(x["one_frame_ordering"] for x in mismatches)
 return {"protocol":"bond_alias_update_order_v1_8_15","source":"bond_position_v1_8_13",
   "session":sid,"frames":len(order),"vector_frames":len(valid),
   "divergence_frames":mismatches,"divergence_count":len(mismatches),
   "change_events":len(changed_events),"phase_summary":phase_summary,
   "ordering_counts":dict(orderings),"ordering_validated":False,
   "permanent_alias_validated":False,
   "notes":["Two components are compared jointly as raw 8-byte vectors.",
     "Event-conditioned update counts exclude unchanged frames; addresses read sequentially per frame.",
     "A lag diagnosis is not evidence of intra-frame write order.",
     "Frozen soldier identity and physical coordinate axes remain unvalidated."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"));a=p.parse_args()
 r=audit(a.session,a.root);out=a.root/f"bond_alias_v1_8_15_{a.session}_analysis.json"
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Alias v1.8.15",out,"divergence frames",r["divergence_count"],"change events",r["change_events"])
if __name__=="__main__":main()
