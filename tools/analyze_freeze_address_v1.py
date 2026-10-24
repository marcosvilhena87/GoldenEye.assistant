"""Compare System Bus alias candidates across freeze OFF/ON phases."""
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path
def analyze(path):
    grouped=defaultdict(lambda:defaultdict(list))
    with Path(path).open(newline="",encoding="utf8") as f:
        for row in csv.DictReader(f):
            if row["phase"] in ("OFF1","ON1","OFF2","ON2"):
                grouped[row["candidate"]][row["phase"]].append(row)
    result=[]
    for candidate,phases in grouped.items():
        values={}
        for phase in ("OFF1","ON1","OFF2","ON2"):
            rows=phases[phase]
            ok=[x["value_u8"] for x in rows if x["read_ok"]=="1"]
            values[phase]={"samples":len(rows),"readable":len(ok),
                          "distribution":dict(Counter(ok))}
        observed=all(values[p]["readable"]>0 for p in values)
        matches=observed and all(
            values[p]["readable"]==values[p]["samples"] and
            set(values[p]["distribution"])==({"0"} if p.startswith("OFF") else {"255"})
            for p in values)
        result.append({"candidate":candidate,"phases":values,
                       "matches_operator_observation":matches,
                       "warning":"Matching states alone does not validate physical alias or causal semantics"})
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--output")
    a=p.parse_args()
    res=analyze(a.csv)
    payload={"source":a.csv,"results":res,"status":"candidate_only"}
    print(json.dumps(payload,indent=2,ensure_ascii=False))
    if a.output:
        out=Path(a.output)
        if out.exists():raise FileExistsError(out)
        out.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf8")
if __name__=="__main__": main()
