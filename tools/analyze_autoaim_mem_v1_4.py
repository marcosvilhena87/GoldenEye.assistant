"""Temporal summary: observed changes and labelled windows, without causal claims."""
import argparse,csv
from collections import Counter,defaultdict
from pathlib import Path
def summarize(timeline,markers):
    with open(timeline,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    with open(markers,newline="",encoding="utf-8") as f: marks=list(csv.DictReader(f))
    if not rows:raise ValueError("Empty timeline")
    session={r["session"] for r in rows}
    if len(session)!=1:raise ValueError("Mixed sessions")
    by=defaultdict(list)
    for row in rows:
        offset=row["offset_hex"];frame=int(row["frame"]);val=int(row["byte"])
        if not 0<=val<=255:raise ValueError("Invalid byte")
        by[offset].append((frame,val))
    out=[]
    for offset,vals in sorted(by.items()):
        vals.sort()
        changes=sum(a[1]!=b[1] for a,b in zip(vals,vals[1:]))
        out.append(dict(offset_hex=offset,samples=len(vals),changes=changes,
                        distinct_values=len({v for _,v in vals}),first_value=vals[0][1],last_value=vals[-1][1]))
    for mark in marks:
        if mark["session"] not in session:raise ValueError("Mismatched event session")
    return out,marks
def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--directory",default="output/csv")
    a=p.parse_args()
    if not a.session.replace("_","").isalnum():p.error("Bad session")
    root=Path(a.directory);prefix=root/f"autoaim_mem_v1_4_{a.session}"
    rows,markers=summarize(str(prefix)+"_timeline.csv",str(prefix)+"_markers.csv")
    out=str(prefix)+"_summary.csv"
    with open(out,"x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("Summary:",out)
    for r in rows:print(r)
    print("Markers:",len(markers),"— operator labels are not independently validated.")
if __name__=="__main__":main()
