"""Enemy Coordinate Discovery v1.1: rank ALL candidates and inspect proximity.
Read-only, exploratory. Scores measure screening priority, NOT probability of XYZ.
"""
import argparse
import csv
import json
import math
import struct
from collections import defaultdict
from pathlib import Path
from tools.analyze_enemy_freeze_v1 import load_manifest, pairs

SIZE = 8388608
FIELDS = ["rank","offset_hex","offset_int","encoding","p1","p2","delta",
          "abs_delta","score","cluster_id","neighbors_16","neighbors_64",
          "plausible_scale","raw_p1","raw_p2"]
def enumerate_candidates(blobs):
    if len(blobs)!=4 or any(len(blob)!=SIZE for blob in blobs):
        raise ValueError("Requires exactly four full 8-MiB snapshots")
    a,h,b,j=blobs
    for offset in range(0,SIZE,4):
        x,y,z,w=(v[offset:offset+4] for v in (a,h,b,j))
        if x!=y or z!=w or x==z: continue
        for endian,label in ((">", "big"),("<","little")):
            p1,p2=struct.unpack(endian+"f",x)[0],struct.unpack(endian+"f",z)[0]
            if not (math.isfinite(p1) and math.isfinite(p2)):continue
            if max(abs(p1),abs(p2))>=1e7 or abs(p1-p2)<1e-5:continue
            yield dict(offset_int=offset,offset_hex=f"0x{offset:06X}",
                encoding="float32_"+label,p1=p1,p2=p2,delta=p2-p1,
                abs_delta=abs(p2-p1),raw_p1=x.hex().upper(),raw_p2=z.hex().upper())

def build_reports(items,max_neighbors=64):
    rows=list(items)
    offsets=sorted(set(r["offset_int"] for r in rows))
    from bisect import bisect_left,bisect_right
    for r in rows:
        o=r["offset_int"]
        r["neighbors_16"]=bisect_right(offsets,o+16)-bisect_left(offsets,o-16)-1
        r["neighbors_64"]=bisect_right(offsets,o+max_neighbors)-bisect_left(offsets,o-max_neighbors)-1
        r["plausible_scale"]=int(1e-3<=abs(r["delta"])<=10000 and
                max(abs(r["p1"]),abs(r["p2"]))<=100000)
        # Heuristic preference for nearby co-changing values, plausible magnitudes,
        # and BE representation. Not calibrated; reflects analyst triage only.
        r["score"]=round(2*r["plausible_scale"]+
                         min(r["neighbors_16"],4)*1.5+
                         min(r["neighbors_64"],12)*0.25+
                         (1 if r["encoding"]=="float32_big" else 0),2)
    ordered=sorted(rows,key=lambda r:(-r["score"],r["offset_int"],r["encoding"]))
    for i,r in enumerate(ordered,1):r["rank"]=i
    clusters=[]
    if offsets:
        groups=[[offsets[0]]]
        for o in offsets[1:]:
            if o-groups[-1][-1]<=64:groups[-1].append(o)
            else:groups.append([o])
        cluster_by_offset={}
        for n,g in enumerate(groups,1):
            cid=f"C{n:04d}"
            for o in g:cluster_by_offset[o]=cid
            members=[r for r in ordered if r["offset_int"] in set(g)]
            clusters.append(dict(cluster_id=cid,start_hex=f"0x{g[0]:06X}",
                end_hex=f"0x{g[-1]:06X}",distinct_offsets=len(g),
                interpretations=len(members),
                big_count=sum(r["encoding"]=="float32_big" for r in members),
                little_count=sum(r["encoding"]=="float32_little" for r in members),
                best_score=max(r["score"] for r in members),
                status="proximity_only"))
        for r in ordered:r["cluster_id"]=cluster_by_offset[r["offset_int"]]
    clusters.sort(key=lambda x:(-x["distinct_offsets"],-x["best_score"],x["start_hex"]))
    # Pairs are limited to nearby DIFFERENT offsets of same encoding.
    # No assumption these are X/Y axes; two snapshots cannot establish independence.
    by_offset=defaultdict(list)
    for r in ordered:by_offset[r["offset_int"]].append(r)
    pairrows=[]
    for o in offsets:
        for p in offsets[bisect_right(offsets,o):bisect_right(offsets,o+16)]:
            for a in by_offset[o]:
                for b in by_offset[p]:
                    if a["encoding"]!=b["encoding"]:continue
                    pairrows.append(dict(offset_a=a["offset_hex"],offset_b=b["offset_hex"],
                        gap_bytes=p-o,encoding=a["encoding"],delta_a=a["delta"],
                        delta_b=b["delta"],screening_score=round(a["score"]+b["score"],2),
                        status="proximity_only_not_axes"))
    pairrows.sort(key=lambda x:(-x["screening_score"],x["offset_a"],x["offset_b"]))
    return ordered,clusters,pairrows

def write_csv(path,rows,fields):
    with path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)

def execute(session,root,output=None):
    manifest=root/"output/csv"/f"enemy_freeze_v1_{session}_manifest.csv"
    rows=load_manifest(manifest)
    selection,error=pairs(rows)
    if error:raise ValueError(error)
    file_rows=[selection[0][1]["on_stable"],selection[0][1]["on_hold"],
               selection[1][1]["on_stable"],selection[1][1]["on_hold"]]
    blobs=[(root/r["file"]).read_bytes() for r in file_rows]
    ranked,clusters,ps=build_reports(enumerate_candidates(blobs))
    folder=output or root/"output/csv"
    folder.mkdir(parents=True,exist_ok=True)
    prefix=f"enemy_freeze_v1_1_{session}"
    paths={kind:folder/(prefix+"_"+kind+".csv") for kind in
           ("candidate_ranking","spatial_clusters","candidate_pairs")}
    summary=folder/(prefix+"_summary.json")
    if any(p.exists() for p in list(paths.values())+[summary]):
        raise FileExistsError("Refusing overwrite of an existing report")
    write_csv(paths["candidate_ranking"],ranked,FIELDS)
    write_csv(paths["spatial_clusters"],clusters,
        ["cluster_id","start_hex","end_hex","distinct_offsets","interpretations",
         "big_count","little_count","best_score","status"])
    write_csv(paths["candidate_pairs"],ps,
        ["offset_a","offset_b","gap_bytes","encoding","delta_a","delta_b",
         "screening_score","status"])
    data=dict(status="candidate_only",session=session,
        on_epochs=[selection[0][0],selection[1][0]],
        candidates=len(ranked),clusters=len(clusters),pairs=len(ps),
        raw_files=[r["file"] for r in file_rows],
        notes=["Ranking is a heuristic, NOT evidence of physical XYZ.",
               "Nearby offsets and candidate pairs are not proof of an object structure.",
               "Uses only first two ON epochs; no independent movement direction.",
               "KSEG0/RDRAM equivalence and ROM/core identity remain unverified."],
        paths={k:str(v) for k,v in paths.items()})
    summary.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("session_id")
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(execute(a.session_id,a.root),indent=2,ensure_ascii=False))
