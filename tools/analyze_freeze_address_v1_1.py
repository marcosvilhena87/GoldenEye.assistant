"""Analyze automatic freeze transitions; never assign coordinate or validated status."""
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path

def analyze(timeline,events,termination):
    per_frame=defaultdict(dict)
    counts=Counter()
    with Path(timeline).open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            frame=int(row["frame"]);key=row["candidate"]
            if key in per_frame[frame]: raise ValueError("Duplicate candidate/frame")
            per_frame[frame][key]=row
            counts[key+"_samples"]+=1
    mismatch=[];actual=Counter()
    for frame,rows in sorted(per_frame.items()):
        a=rows.get("kseg0_alias");b=rows.get("kseg1_alias")
        if not a or not b or a["read_ok"]!="1" or b["read_ok"]!="1" or a["value_u8"]!=b["value_u8"] or a["value_u8"] not in ("0","255"):
            mismatch.append(frame)
        else: actual["OFF" if a["value_u8"]=="0" else "ON"]+=1
    with Path(events).open(newline="",encoding="utf-8") as f:
        observed=list(csv.DictReader(f))
    with Path(termination).open(newline="",encoding="utf-8") as f:
        ends=list(csv.DictReader(f))
    changes=[{"confirmed_at_frame":int(e["frame"]),
              "first_observed_frame":int(e["run_start_frame"]),
              "from":e["from_state"],"to":e["to_state"],
              "confirmation_delay_frames":int(e["frame"])-int(e["run_start_frame"])}
             for e in observed if e["event"]=="TRANSITION_CONFIRMED"]
    return {"frames":len(per_frame),"counts":dict(counts),
       "agreed_states":dict(actual),"mismatched_or_unknown_frames":len(mismatch),
       "first_mismatch_frames":mismatch[:20],"transitions":changes,
       "events_by_type":dict(Counter(e["event"] for e in observed)),
       "termination":ends,"status":"candidate_only",
       "caveats":["On/off state is inferred from equal KSEG aliases, not verified with RAM Watch per frame",
                  "No ROM/core identity or enemy XYZ validation",
                  "Confirmation is retrospective by stable-frame threshold"]}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("session_id")
    ap.add_argument("--root",type=Path,default=Path("."))
    args=ap.parse_args()
    stem="freeze_address_v1_1_"+args.session_id
    base=args.root/"output/csv"
    result=analyze(base/(stem+"_timeline.csv"),base/(stem+"_events.csv"),base/(stem+"_termination.csv"))
    dst=base/(stem+"_analysis.json")
    if dst.exists(): raise FileExistsError(dst)
    dst.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
