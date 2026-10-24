"""v1.5 Field Alignment & Record Layout Validation — exploratory read-only analysis."""
import argparse
import csv
import json
from pathlib import Path
try:
    from tools.analyze_enemy_freeze_v1 import load_manifest, pairs
    from tools.analyze_enemy_freeze_v1_2 import SIZE, START, END, SHIFT
except ModuleNotFoundError as exc:
    if exc.name!="tools": raise
    from analyze_enemy_freeze_v1 import load_manifest, pairs
    from analyze_enemy_freeze_v1_2 import SIZE, START, END, SHIFT

STRIDES=(0x40,0x48,0x50)
CONTROLS=(0x44,0x4C,0x54)
WIDTHS=(2,4,8)
def field_events(blobs,start=START,end=END):
    """For every fully aligned word, return ON stability and P1->P2 changes."""
    if len(blobs)!=4 or any(len(v)!=SIZE for v in blobs):
        raise ValueError("Four full 8MiB captures required")
    if not 0<=start<end<=SIZE:raise ValueError("Invalid window")
    a,ah,b,bh=blobs
    results=[]
    for width in WIDTHS:
        for o in range(((start+width-1)//width)*width,end-width+1,width):
            p1=a[o:o+width];p1h=ah[o:o+width]
            p2=b[o:o+width];p2h=bh[o:o+width]
            stable=p1==p1h and p2==p2h
            changed=p1!=p2
            results.append(dict(offset=o,width=width,stable=stable,changed=changed,
                                p1=p1.hex().upper(),p2=p2.hex().upper()))
    return results

def profile(events,start=START,strides=STRIDES+CONTROLS):
    """Compare word-level *change patterns*, NOT equal values or numeric deltas."""
    summary=[];phase_rows=[]
    for stride in strides:
        for width in WIDTHS:
            subset={e["offset"]:e for e in events if e["width"]==width}
            phase={}
            for o,e in subset.items():
                other=subset.get(o+stride)
                if other is None:continue
                p=(o-start)%stride
                stats=phase.setdefault(p,dict(pairs=0,both_stable=0,both_changed=0,
                                                same_p1=0,same_p2=0))
                stats["pairs"]+=1
                if e["stable"] and other["stable"]:
                    stats["both_stable"]+=1
                    if e["changed"] and other["changed"]:
                        stats["both_changed"]+=1
                    if e["p1"]==other["p1"]: stats["same_p1"]+=1
                    if e["p2"]==other["p2"]: stats["same_p2"]+=1
            allstats=dict(pairs=sum(x["pairs"] for x in phase.values()),
                both_stable=sum(x["both_stable"] for x in phase.values()),
                both_changed=sum(x["both_changed"] for x in phase.values()),
                same_p1=sum(x["same_p1"] for x in phase.values()),
                same_p2=sum(x["same_p2"] for x in phase.values()))
            denom=allstats["both_stable"]
            summary.append(dict(stride_hex=f"0x{stride:X}",stride_bytes=stride,
                is_control=int(stride in CONTROLS),field_width=width,**allstats,
                repeated_change_rate=round(allstats["both_changed"]/denom,6) if denom else 0,
                exact_both_epoch_rate=round(min(allstats["same_p1"],allstats["same_p2"])/denom,6) if denom else 0))
            for p,x in sorted(phase.items()):
                phase_rows.append(dict(stride_hex=f"0x{stride:X}",field_width=width,
                    phase=p,**x))
    return summary,phase_rows

def analyze(blobs,start=START,end=END,shift=SHIFT):
    if end+shift>SIZE:raise ValueError("Shift exceeds dumps")
    events_a=field_events(blobs,start,end)
    events_b=field_events(blobs,start+shift,end+shift)
    records=[]
    phases=[]
    for region,events,origin in (("A",events_a,start),("B",events_b,start+shift)):
        r,p=profile(events,origin)
        for item in r:item["region"]=region
        for item in p:item["region"]=region
        records.extend(r);phases.extend(p)
    return records,phases

def write_csv(path,rows):
    if not rows:raise ValueError("No rows")
    with path.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def execute(session,root=Path(".")):
    root=Path(root)
    chosen,error=pairs(load_manifest(root/"output/csv"/f"enemy_freeze_v1_{session}_manifest.csv"))
    if error:raise ValueError(error)
    rows=[chosen[0][1]["on_stable"],chosen[0][1]["on_hold"],
          chosen[1][1]["on_stable"],chosen[1][1]["on_hold"]]
    for r in rows:
        if r["state"]!="ON" or r["frame"]!=r["frame_after"] or r["notes"]!="raw_bus_kseg0_unvalidated":
            raise ValueError("Invalid capture metadata")
    blobs=[(root/r["file"]).read_bytes() for r in rows]
    ranking,phases=analyze(blobs)
    output=root/"output/csv"
    prefix=f"enemy_freeze_v1_5_{session}"
    ranks=output/(prefix+"_field_stride_ranking.csv")
    profiles=output/(prefix+"_field_phase_profiles.csv")
    summary=output/(prefix+"_summary.json")
    if any(p.exists() for p in (ranks,profiles,summary)):
        raise FileExistsError("v1.5 files already exist; no overwrite")
    write_csv(ranks,ranking)
    write_csv(profiles,phases)
    report=dict(status="field_layout_candidate_only",session=session,
        epochs=[chosen[0][0],chosen[1][0]],window=[f"0x{START:X}",f"0x{END:X}"],
        mirror_shift_hex=f"0x{SHIFT:X}",strides=[f"0x{s:X}" for s in STRIDES],
        controls=[f"0x{s:X}" for s in CONTROLS],word_widths=list(WIDTHS),
        rows=len(ranking),ranking=ranking,
        caveats=["Word alignment is absolute to KSEG0 offset; field offsets remain hypotheses.",
                 "Matching stable changes not necessarily matching movement direction or numeric delta.",
                 "Two ON epochs only; no enemy-instance identity or XYZ ground truth.",
                 "Control strides may overlap real periods and are not statistical independence controls."])
    summary.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session_id");p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    out=execute(args.session_id,args.root)
    print(json.dumps({k:v for k,v in out.items() if k!="ranking"},indent=2,ensure_ascii=False))
if __name__=="__main__":main()
