"""Bond–Soldier v1.8.4: freeze transition and motion episode audit; read-only."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

FIELDS = ("bond_e8","bond_ec","bond_f0","bond_f4","soldier_1_a","soldier_1_b","freeze_indicator_candidate")
SOLDIER = ("soldier_1_a","soldier_1_b")
def load(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))
def episodes(frames, max_quiet=12):
    """Cluster event frames; event gap > max_quiet begins a new episode."""
    chunks=[]
    for n in sorted(set(frames)):
        if not chunks or n-chunks[-1]["last"]>max_quiet:
            chunks.append({"first":n,"last":n,"events":1})
        else:
            chunks[-1]["last"]=n
            chunks[-1]["events"]+=1
    return chunks
def analyze(sid,root=Path("output/csv"),max_quiet=12,settle_frames=120):
    if not sid or any(x in sid for x in ("/","\\","..","\n")):raise ValueError("unsafe session")
    if max_quiet<1 or settle_frames<1:raise ValueError("invalid windows")
    stem=root/("bond_soldier_v1_8_4_"+sid)
    data=load(Path(str(stem)+"_timeline.csv"))
    marks=load(Path(str(stem)+"_markers.csv"))
    ends=load(Path(str(stem)+"_termination.csv"))
    if not data:raise ValueError("empty timeline")
    frames={}
    aliases=[]
    for row in data:
        if row["session"]!=sid or row["field"] not in FIELDS:raise ValueError("invalid row")
        n=int(row["frame"])
        if row["field"] in frames.setdefault(n,{}):raise ValueError("duplicate field")
        frames[n][row["field"]]=row
        if row["alias_equal"]!="1":aliases.append([n,row["field"]])
    full=sorted(frames)
    incomplete=[{"frame":n,"missing":sorted(set(FIELDS)-set(frames[n]))}
                for n in full if set(frames[n])!=set(FIELDS)]
    if any(e["frame"]!=full[-1] for e in incomplete):
        raise ValueError("incomplete interior frame")
    if incomplete:del frames[full[-1]]
    seq=sorted(frames)
    if not seq:raise ValueError("no complete frames")
    gaps=[[a,b] for a,b in zip(seq,seq[1:]) if b!=a+1]
    changes=[]
    for a,b in zip(seq,seq[1:]):
        if b!=a+1:continue
        for field in FIELDS:
            x,y=frames[a][field]["kseg0_hex"],frames[b][field]["kseg0_hex"]
            if x!=y:changes.append({"frame":b,"phase":frames[b][field]["phase"],
                                    "field":field,"from":x,"to":y})
    grouped=Counter((x["phase"],x["field"]) for x in changes)
    episode_list={}
    for field in SOLDIER:
        episode_list[field]=episodes([x["frame"] for x in changes if x["field"]==field],max_quiet)
    joint=episodes([x["frame"] for x in changes if x["field"] in SOLDIER],max_quiet)
    markers=[{"frame":int(x["frame"]),"label":x["label"]} for x in marks]
    freeze_changes=[x for x in changes if x["field"]=="freeze_indicator_candidate"]
    bounds=list(seq)
    last=bounds[-1]
    transition=[]
    for index,mark in enumerate(markers):
        if mark["label"] not in ("FREEZE_ON","FREEZE_OFF","SOLDIER_REFROZEN","FREEZE_REQUEST_ON","FREEZE_REQUEST_OFF"):
            continue
        start=mark["frame"]
        end=markers[index+1]["frame"]-1 if index+1<len(markers) else last
        end=min(end,last)
        relevant=[x["frame"] for x in changes if x["field"] in SOLDIER and start<=x["frame"]<=end]
        last_event=max(relevant) if relevant else None
        stable_from=(last_event+1 if last_event is not None else start)
        window_available=(stable_from+settle_frames-1<=end and
                          all(n in frames for n in range(stable_from,stable_from+settle_frames)))
        quiet=bool(window_available and not any(stable_from<=n<stable_from+settle_frames for n in relevant))
        indicator_start=frames.get(start,{}).get("freeze_indicator_candidate")
        indicator_end=frames.get(end,{}).get("freeze_indicator_candidate")
        transition.append({"label":mark["label"],"marker_frame":start,
          "phase_end":end,"last_soldier_change":last_event,
          "first_quiet_frame":stable_from,"delay_from_marker_frames":stable_from-start,
          "complete_quiet_window":window_available,
          "quiet_window_after_last_change":quiet,
          "indicator_at_marker":indicator_start["kseg0_hex"] if indicator_start else None,
          "indicator_at_phase_end":indicator_end["kseg0_hex"] if indicator_end else None,
          "interpretation":"temporal_observation_only"})
    clean=bool(ends and ends[-1].get("reason")=="stop" and not incomplete and not gaps and not aliases)
    return {"protocol":"bond_soldier_freeze_transition_v1_8_4","session":sid,
        "frames":len(seq),"capture_complete":clean,
        "termination":ends,"incomplete_frames":incomplete,"timeline_gaps":gaps,
        "alias_mismatches":aliases,"markers":markers,
        "changes_by_phase_field":[{"phase":p,"field":f,"count":n} for (p,f),n in sorted(grouped.items())],
        "soldier_episodes":episode_list,"joint_soldier_episodes":joint,
        "freeze_indicator_transitions":freeze_changes,
        "freeze_marker_timing":transition,
        "independent_visual_observation_verified":False,
        "soldier_coordinate_validated":False,"freeze_indicator_validated":False,
        "canonical_symbol_promoted":False,
        "limitations":["Markers document operator intent, not physical cheat activation.",
           "Indicator 0x02C90C is provisional and read as u8, never as world coordinate.",
           "Episode gap is a configurable heuristic, not a causal inference.",
           "The quiet-window measurement is bounded by the next marker.",
           "An after-the-fact quiet window does not prove that the guard was frozen.",
           "No same-frame independent camera/geometry/identity evidence is supplied."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("output/csv"))
    p.add_argument("--output",type=Path)
    p.add_argument("--max-quiet",type=int,default=12)
    p.add_argument("--settle-frames",type=int,default=120)
    a=p.parse_args()
    result=analyze(a.session,a.root,a.max_quiet,a.settle_frames)
    out=a.output or a.root/("bond_soldier_v1_8_4_"+a.session+"_analysis.json")
    if out.exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Freeze transition v1.8.4:",out,"frames:",result["frames"],
          "episodes:",len(result["joint_soldier_episodes"]),"complete:",result["capture_complete"])
if __name__=="__main__":main()
