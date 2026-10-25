"""v1.8.6 temporal correlation of experimental Soldier structures (read-only)."""
import argparse,csv,json,struct,math
from pathlib import Path
from collections import defaultdict,Counter
def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def corr(a,b):
    if len(a)<3:return None
    x=sum(a)/len(a);y=sum(b)/len(b)
    xx=sum((v-x)**2 for v in a);yy=sum((v-y)**2 for v in b)
    return sum((p-x)*(q-y) for p,q in zip(a,b))/math.sqrt(xx*yy) if xx>0 and yy>0 else None
def analyze(sid,root=Path("output/csv"),limit=80):
    if not sid or any(x in sid for x in ("/","\\","..","\r","\n")):raise ValueError("invalid SID")
    base=root/("soldier_spatial_v1_8_6_"+sid)
    rows=read(Path(str(base)+"_timeline.csv"));marks=read(Path(str(base)+"_markers.csv"));end=read(Path(str(base)+"_termination.csv"))
    if not rows:raise ValueError("empty timeline")
    byoffset=defaultdict(dict); phases={};seen=set()
    for r in rows:
        if r["session"]!=sid:raise ValueError("wrong session")
        n=int(r["frame"]);o=int(r["offset_hex"],16)
        if (n,o) in seen:raise ValueError("duplicate sample")
        seen.add((n,o));byoffset[o][n]=r["raw_be"]
        if n in phases and phases[n]!=r["phase"]:raise ValueError("mixed phases")
        phases[n]=r["phase"]
    offsets=sorted(byoffset); frames=sorted(phases)
    incomplete=[n for n in frames if any(n not in byoffset[o] for o in offsets)]
    if incomplete and incomplete!=[frames[-1]]:raise ValueError("incomplete interior frame")
    if incomplete:
        for o in offsets:byoffset[o].pop(frames[-1],None)
        frames.pop()
    gaps=[[a,b] for a,b in zip(frames,frames[1:]) if b!=a+1]
    stats=[];changed_frames={};series={}
    for o in offsets:
        values=[byoffset[o][n] for n in frames]
        changed={frames[i] for i in range(1,len(frames)) if frames[i]==frames[i-1]+1 and values[i]!=values[i-1]}
        changed_frames[o]=changed
        series[o]=values
        perphase=Counter(phases[n] for n in changed)
        decoded=[]
        for v in values:
            x=struct.unpack(">f",bytes.fromhex(v))[0]
            decoded.append(x if math.isfinite(x) and abs(x)<1e8 else None)
        stats.append({"offset_hex":f"0x{o:06X}","total_changes":len(changed),
                      "by_phase":dict(perphase),"unique_values":len(set(values)),
                      "plausible_float32_be":sum(x is not None for x in decoded)==len(decoded)})
    pairs=[]
    for i,o in enumerate(offsets):
        for p in offsets[i+1:]:
            union=changed_frames[o]|changed_frames[p]
            inter=changed_frames[o]&changed_frames[p]
            if not union:continue
            j=len(inter)/len(union)
            if j<0.7:continue
            same=sum(a==b for a,b in zip(series[o],series[p]))/len(frames)
            distances=[]
            for a,b in zip(series[o],series[p]):
                x=struct.unpack(">f",bytes.fromhex(a))[0];y=struct.unpack(">f",bytes.fromhex(b))[0]
                if math.isfinite(x) and math.isfinite(y) and abs(x)<1e8 and abs(y)<1e8:distances.append(y-x)
            constdelta=(max(distances)-min(distances)<0.001) if len(distances)==len(frames) else False
            pairs.append({"a":f"0x{o:06X}","b":f"0x{p:06X}","cochange_jaccard":round(j,5),
                         "same_raw_fraction":round(same,5),"constant_float_offset":constdelta,
                         "float_offset":round(distances[0],6) if constdelta else None})
    pairs.sort(key=lambda x:(-x["cochange_jaccard"],-x["same_raw_fraction"],x["a"],x["b"]))
    clean=bool(end and end[-1]["reason"]=="stop" and not incomplete and not gaps)
    return {"protocol":"soldier_spatial_v1_8_6","session":sid,"frames":len(frames),
            "capture_complete":clean,"incomplete_frames":incomplete,"gaps":gaps,
            "termination":end,"markers":[{"frame":int(x["frame"]),"label":x["label"]} for x in marks],
            "field_stats":stats,"pair_count":len(pairs),"top_pairs":pairs[:limit],
            "xyz_validated":False,"stable_across_saves":False,"entity_identity_verified":False,
            "notes":["Equal transition times or float offsets may reflect copies or derived state, not physical coordinates.",
                     "SOLDIER_FREEZE phase is operator-marked, not a verified cheat state.",
                     "No cross-save address resolution or independent measured geometry."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("session");p.add_argument("--root",type=Path,default=Path("output/csv"))
    p.add_argument("--limit",type=int,default=80);p.add_argument("--output",type=Path)
    a=p.parse_args();r=analyze(a.session,a.root,a.limit)
    out=a.output or a.root/f"soldier_spatial_v1_8_6_{a.session}_analysis.json"
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Spatial v1.8.6:",out,"frames:",r["frames"],"pairs:",r["pair_count"],"complete:",r["capture_complete"])
if __name__=="__main__":main()
