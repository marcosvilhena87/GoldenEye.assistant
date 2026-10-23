"""Independent validation of two or more complete v1.3 sessions (read-only)."""
import argparse
import csv
from pathlib import Path

LABELS=("ON_BASE","ON_STABLE","OFF1","OFF_STABLE","ON2",
        "MENU_CONTROL","OTHER_OPTION_CONTROL","NO_TARGET_ON")
ON=("ON_BASE","ON_STABLE","ON2","MENU_CONTROL","OTHER_OPTION_CONTROL","NO_TARGET_ON")
OFF=("OFF1","OFF_STABLE")
OFFSETS=("0x040A93","0x067D37","0x069AAD","0x0D308B","0x0D309B")

def read_session(samples_path, manifest_path):
    with manifest_path.open(newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=len(LABELS) or tuple(r["label"] for r in rows)!=LABELS:
        raise ValueError("Manifest incomplete or out of order: "+str(manifest_path))
    sessions={r["session"] for r in rows}
    if len(sessions)!=1 or any(r["domain"]!="RDRAM" or int(r["count"])!=5 for r in rows):
        raise ValueError("Manifest metadata invalid")
    sid=next(iter(sessions))
    by_offset={offset:{} for offset in OFFSETS}
    count=0
    with samples_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            offset=r["offset_hex"]
            if r["session"]!=sid or r["domain"]!="RDRAM" or offset not in by_offset or r["label"] not in LABELS:
                raise ValueError("Sample metadata invalid")
            if r["label"] in by_offset[offset]:
                raise ValueError("Duplicate reading")
            manifest_row=rows[LABELS.index(r["label"])]
            if int(r["frame"])!=int(manifest_row["frame"]):
                raise ValueError("Frame mismatch")
            byte=int(r["byte"])
            if not 0<=byte<=255:raise ValueError("Byte out of range")
            by_offset[offset][r["label"]]=byte
            count+=1
    if count!=40 or any(set(d)!=set(LABELS) for d in by_offset.values()):
        raise ValueError("Missing/extra samples")
    return sid,by_offset

def analyze(sessions):
    report=[]
    for offset in OFFSETS:
        per=[]
        for sid, data in sessions:
            d=data[offset]
            stable_on=len({d[x] for x in ON})==1
            stable_off=len({d[x] for x in OFF})==1
            separating=d["ON_BASE"]!=d["OFF1"]
            per.append((sid,stable_on and stable_off and separating,d["ON_BASE"],d["OFF1"]))
        reproduced=(len(per)>=2 and all(x[1] for x in per)
                    and len({(x[2],x[3]) for x in per})==1)
        report.append({"offset_hex":offset,"status":"reproduced_candidate_controls_only" if reproduced else "needs_validation",
                       "runs":len(per),"details":";".join(f"{x[0]}:{int(x[1])}:ON={x[2]}:OFF={x[3]}" for x in per)})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("sessions",nargs="+",help="session IDs (at least two independent runs)")
    p.add_argument("--directory",default="output/csv")
    p.add_argument("--output",default=None)
    args=p.parse_args()
    if len(set(args.sessions))!=len(args.sessions) or len(args.sessions)<2:
        p.error("Provide two distinct, independently captured session IDs")
    root=Path(args.directory)
    sessions=[]
    for sid in args.sessions:
        if not sid.replace("_","").isalnum():p.error("Unsafe session ID")
        samples=root/f"autoaim_mem_v1_3_samples_{sid}.csv"
        manifest=root/f"autoaim_mem_v1_3_manifest_{sid}.csv"
        sessions.append(read_session(samples,manifest))
    rows=analyze(sessions)
    out=Path(args.output) if args.output else root/"autoaim_mem_v1_3_independent_validation.csv"
    if out.exists():raise SystemExit("Refusing to overwrite report: "+str(out))
    with out.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=("offset_hex","status","runs","details"))
        writer.writeheader();writer.writerows(rows)
    print("Wrote",out,"reproduced",sum(r["status"]=="reproduced_candidate_controls_only" for r in rows))
    print("Experimental only: no validated addresses, RAM writes, or auto-aim control.")
if __name__=="__main__":
    main()
