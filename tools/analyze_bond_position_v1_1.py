#!/usr/bin/env python3
"""Audit Bond Position v1.1 CSV: descriptive evidence, not axis validation."""
import csv, collections, json, math, pathlib, statistics, sys
def analyze(sid,root=pathlib.Path("output/csv")):
    base=root/("bond_position_v1_1_"+sid)
    path=pathlib.Path(str(base)+"_timeline.csv")
    groups=collections.defaultdict(list)
    alias_bad=nonfinite=rows=0
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["session"]!=sid: raise ValueError("Session ID mismatch")
            rows+=1
            alias_bad+=r["alias_equal"]!="1"
            nonfinite+=r["finite"]!="1"
            if r["finite"]=="1":
                v=float(r["float32_be"])
                if math.isfinite(v): groups[(r["phase"],r["offset_hex"])].append((int(r["frame"]),v))
    result={"session":sid,"rows":rows,"alias_mismatches":alias_bad,"nonfinite":nonfinite,"phases":[],"interpretation":"Descriptive only: no axis or write persistence validation without physical intervention annotations."}
    for (phase,offset),pairs in sorted(groups.items()):
        values=[v for _,v in pairs]
        result["phases"].append({"phase":phase,"offset_hex":offset,"samples":len(values),"min":min(values),"max":max(values),"first":values[0],"last":values[-1],"delta":values[-1]-values[0],"median":statistics.median(values),"distinct_values":len(set(values))})
    term=pathlib.Path(str(base)+"_termination.csv")
    if term.exists():
        with term.open(newline="",encoding="utf-8") as f:
            result["termination"]=list(csv.DictReader(f))
    result["flags"]={"alias_equivalence_observed":alias_bad==0 and rows>0,"clean_stop":bool(result.get("termination")) and result["termination"][-1]["reason"]=="stop","axis_validated":False,"write_persistence_validated":False}
    output=pathlib.Path(str(base)+"_analysis.json")
    if output.exists(): raise FileExistsError(output)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return output,result
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: python -m tools.analyze_bond_position_v1_1 SESSION_ID")
    out,r=analyze(sys.argv[1])
    print("Audit:",out,"rows:",r["rows"],"alias_mismatches:",r["alias_mismatches"],"clean_stop:",r["flags"]["clean_stop"])
