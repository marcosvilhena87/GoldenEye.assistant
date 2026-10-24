"""Spatial v2.1: offline 32-bit layout interpretations and temporal pattern probes.

Consumes independently verified v1.9 session via v2.0.validate().
No address validation, memory writes, or emulator interaction.
"""
import argparse
import csv
import math
import statistics
import struct
from collections import Counter
from pathlib import Path
try:
    from tools.analyze_spatial_position_v2_0 import ADDRS, PHASES, validate
except ModuleNotFoundError:
    from analyze_spatial_position_v2_0 import ADDRS, PHASES, validate

LAYOUT_FIELDS=("session","phase","address","interpretation","n","unique","changes",
               "longest_run","min","max","median","start","end","delta")
LAG_FIELDS=("session","phase","address","lag","comparisons","raw_equal_rate",
            "change_agreement_rate","change_rate")
BYTE_FIELDS=("session","phase","address","byte_index","unique","changes",
             "most_common_hex","most_common_fraction")
CROSS_FIELDS=("session","phase","lag","comparisons","change_agreement_rate",
              "both_change_rate")
MAX_LAG=32

def decode(raw):
    b=bytes.fromhex(raw)
    res={}
    for prefix,end in (("be",">"),("le","<")):
        res[prefix+"_u32"]=struct.unpack(end+"I",b)[0]
        res[prefix+"_i32"]=struct.unpack(end+"i",b)[0]
        res[prefix+"_f32"]=struct.unpack(end+"f",b)[0]
        for j in range(2):
            res[f"{prefix}_u16_{j}"]=struct.unpack(end+"H",b[j*2:j*2+2])[0]
            res[f"{prefix}_i16_{j}"]=struct.unpack(end+"h",b[j*2:j*2+2])[0]
    for j,x in enumerate(b):
        res[f"byte_{j}"]=x
    return res

def runs(values):
    if not values:return 0
    best=cur=1
    for a,b in zip(values,values[1:]):
        cur=cur+1 if a==b else 1
        best=max(best,cur)
    return best

def phase_samples(by_frame,markers):
    result={}
    for idx,phase in enumerate(PHASES):
        frames=list(range(markers[idx],markers[idx+1]))
        if any(f not in by_frame for f in frames):
            raise ValueError("Incomplete phase "+phase)
        result[phase]=frames
    return result

def lag_scores(values,max_lag=MAX_LAG):
    result=[]
    changes=[values[j]!=values[j-1] for j in range(1,len(values))]
    for lag in range(1,min(max_lag,len(values)-1)+1):
        pairs=len(values)-lag
        equal=sum(values[j]==values[j-lag] for j in range(lag,len(values)))/pairs
        c_pairs=max(0,len(changes)-lag)
        agree=(sum(changes[j]==changes[j-lag] for j in range(lag,len(changes)))/c_pairs
               if c_pairs else None)
        result.append((lag,pairs,equal,agree,sum(changes)/len(changes) if changes else 0))
    return result

def cross_scores(a,b,max_lag=MAX_LAG):
    ca=[a[j]!=a[j-1] for j in range(1,len(a))]
    cb=[b[j]!=b[j-1] for j in range(1,len(b))]
    result=[]
    for lag in range(-min(max_lag,len(ca)-1),min(max_lag,len(ca)-1)+1):
        pairs=[(ca[j],cb[j+lag]) for j in range(len(ca)) if 0<=j+lag<len(cb)]
        result.append((lag,len(pairs),
                       sum(x==y for x,y in pairs)/len(pairs),
                       sum(x and y for x,y in pairs)/len(pairs)))
    return result

def audit(session,by_frame,markers,max_lag=MAX_LAG):
    if not 1<=max_lag<=1024:raise ValueError("max_lag out of range")
    layouts,lags,bytes_out,cross=[],[],[],[]
    for phase,frames in phase_samples(by_frame,markers).items():
        for addr in ADDRS:
            raw=[by_frame[f][addr] for f in frames]
            decoded=[decode(x) for x in raw]
            for key in decoded[0]:
                seq=[x[key] for x in decoded]
                finite=[x for x in seq if math.isfinite(x)]
                # Non-finite float interpretations must remain visible but excluded
                # from numerical statistics.
                layouts.append(dict(session=session,phase=phase,address=addr,
                                    interpretation=key,n=len(seq),unique=len(set(seq)),
                                    changes=sum(a!=b for a,b in zip(seq,seq[1:])),
                                    longest_run=runs(seq),min=min(finite) if finite else "",
                                    max=max(finite) if finite else "",
                                    median=statistics.median(finite) if finite else "",
                                    start=seq[0],end=seq[-1],
                                    delta=seq[-1]-seq[0] if all(math.isfinite(x) for x in (seq[0],seq[-1])) else ""))
            for lag,n,equal,agree,rate in lag_scores(raw,max_lag):
                lags.append(dict(session=session,phase=phase,address=addr,lag=lag,
                                 comparisons=n,raw_equal_rate=equal,
                                 change_agreement_rate=agree if agree is not None else "",
                                 change_rate=rate))
            for j in range(4):
                vals=[x[j*2:j*2+2] for x in raw]
                most,count=Counter(vals).most_common(1)[0]
                bytes_out.append(dict(session=session,phase=phase,address=addr,
                                      byte_index=j,unique=len(set(vals)),
                                      changes=sum(a!=b for a,b in zip(vals,vals[1:])),
                                      most_common_hex=most,
                                      most_common_fraction=count/len(vals)))
        a=[by_frame[f][ADDRS[0]] for f in frames]
        b=[by_frame[f][ADDRS[1]] for f in frames]
        for lag,n,agree,both in cross_scores(a,b,max_lag):
            cross.append(dict(session=session,phase=phase,lag=lag,comparisons=n,
                              change_agreement_rate=agree,both_change_rate=both))
    return layouts,lags,bytes_out,cross

def run(session,root,max_lag=MAX_LAG):
    data,markers=validate(session,root)
    reports=audit(session,data,markers,max_lag)
    names=("_layouts.csv","_lag_patterns.csv","_byte_activity.csv","_cross_lag.csv")
    fields=(LAYOUT_FIELDS,LAG_FIELDS,BYTE_FIELDS,CROSS_FIELDS)
    base=root/"output/csv"/("spatial_v2_1_"+session)
    paths=[Path(str(base)+name) for name in names]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite existing v2.1 reports")
    for path,header,rows in zip(paths,fields,reports):
        with path.open("x",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
    return paths,reports

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session")
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--max-lag",type=int,default=MAX_LAG)
    args=p.parse_args()
    paths,reports=run(args.session,args.root.resolve(),args.max_lag)
    for path,rows in zip(paths,reports):
        print(f"Wrote {path} rows={len(rows)}")
    print("Interpretations and lag correlations are exploratory; no coordinates validated.")

if __name__=="__main__":
    main()
