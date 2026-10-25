"""Bond v1.3 write-intervention diagnostics. Never validates physical location automatically."""
import csv,json,math,sys
from pathlib import Path
TARGETS={"0x0D33EC","0x0D33F4"}
def analyze(sid,root=Path("output/csv")):
    stem=root/("bond_position_v1_3_"+sid)
    def rows(end):
        with Path(str(stem)+end).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
    timeline=rows("_timeline.csv");markers=rows("_markers.csv");term=rows("_termination.csv");disc=rows("_discontinuities.csv")
    if not timeline or len(timeline)%4:raise ValueError("incomplete timeline")
    frames={}
    aliasbad=0
    for r in timeline:
        if r["session"]!=sid:raise ValueError("session mismatch")
        frame=int(r["frame"]);off=r["offset_hex"]
        if off in frames.setdefault(frame,{}):raise ValueError("duplicate offset")
        frames[frame][off]=r
        aliasbad+=(r["alias_equal"]!="1")
    if any(len(v)!=4 for v in frames.values()):raise ValueError("missing offsets")
    # A write event is bounded by TARGET, WRITE_PRE, WRITE_APPLIED and WRITE_OBSERVE.
    windows=[];target=None;pre=None
    for m in markers:
        name=m["label"];frame=int(m["frame"])
        if name.startswith("TARGET_"):
            target="0x0D33EC" if name=="TARGET_EC" else "0x0D33F4";pre=None
        elif name=="WRITE_PRE":pre=frame
        elif name=="WRITE_APPLIED":
            item={"target":target,"before_marker":pre,"after_marker":frame,
                  "frame_samples":{},"status":"unverified_manual_write","notes":[]}
            if target not in TARGETS or pre is None or pre>=frame:
                item["notes"].append("missing target or PRE marker")
            else:
                prior=frames.get(frame-1,{}).get(target)
                if prior is None:
                    item["notes"].append("prior frame missing")
                else:
                    item["prior_hex"]=prior["kseg0_hex"]
                    item["prior_float"]=prior["float32_be"]
                    for gap in (0,1,30,120):
                        rec=frames.get(frame+gap,{}).get(target)
                        item["frame_samples"][str(gap)]=None if rec is None else {
                            "hex":rec["kseg0_hex"],"float32_be":rec["float32_be"],
                            "unchanged_from_prior":rec["kseg0_hex"]==prior["kseg0_hex"],
                            "alias_equal":rec["alias_equal"]=="1"}
                    item["notes"].append("frame 0 is first post-marker frame, NOT necessarily actual write frame")
            windows.append(item)
    result={"session":sid,"frames":len(frames),"rows":len(timeline),"alias_mismatches":aliasbad,
            "termination":term,"discontinuities":disc,"write_windows":windows,
            "flags":{"clean_stop":bool(term) and term[-1]["reason"]=="stop",
                     "physical_axis_validated":False,"write_persistence_validated":False},
            "limitations":["Manual intervention timing is not objectively verified","No verified camera/geometry observation","0/1/30/120 are marker-relative observations, not measured write-to-frame timing","Each target requires an independent reset and session"]}
    out=Path(str(stem)+"_analysis.json")
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return out,result
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("python -m tools.analyze_bond_position_v1_3 SESSION_ID")
    p,r=analyze(sys.argv[1]);print("Audit:",p,"frames:",r["frames"],"windows:",len(r["write_windows"]),"aliases:",r["alias_mismatches"],"stop:",r["flags"]["clean_stop"])
