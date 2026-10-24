"""v2.6 offline structural audit of v2.4 RDRAM recordings. No coordinate validation."""
import argparse
import csv
import math
from collections import Counter
from pathlib import Path

try:
    from .analyze_spatial_position_v2_4 import load, PHASES
except ImportError:
    from analyze_spatial_position_v2_4 import load, PHASES

BASES = (0x3B30D0, 0x3B30E0, 0x3B30EC)
WIDTH = 4
LAGS = (1, 2, 3, 6, 13, 19)
BYTE_FIELDS = ("session","phase","base","byte_address","byte_index","frames",
               "unique_values","change_rate","top_hex","top_fraction",
               "longest_constant_run","top_transitions")
SPLIT_FIELDS = ("session","phase","base","part","order","unique_values",
                "change_rate","top_hex","top_fraction")
SYNC_FIELDS = ("session","phase","left","right","frames_compared","both_changed",
               "only_left","only_right","neither","synchrony_given_either",
               "phi","value_equal_fraction")
PERIOD_FIELDS = ("session","phase","address","lag","pairs","raw_match_rate",
                 "independent_match_baseline","excess_match","changed_at_lag_rate")
PATTERN_FIELDS = ("session","phase","base","frames","unique_words","word_change_rate",
                  "most_common_word","most_common_fraction","alternating_aba_fraction",
                  "top_words")

def rate(xs):
    return sum(a != b for a,b in zip(xs,xs[1:])) / max(len(xs)-1,1)

def top(xs, limit=5):
    counts=Counter(xs)
    return ";".join("{}:{}".format(k,n) for k,n in counts.most_common(limit))

def phi(a,b,c,d):
    den=math.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    return (a*d-b*c)/den if den else ""

def phase_arrays(frames, boundaries):
    for i,phase in enumerate(PHASES):
        yield phase,range(boundaries[i],boundaries[i+1])

def audit(session,frames,boundaries):
    byte_rows,split_rows,sync_rows,period_rows,pattern_rows=[],[],[],[],[]
    for phase,span in phase_arrays(frames,boundaries):
        fs=list(span)
        n=len(fs)
        if n<3:
            raise ValueError("Phase {} has fewer than three frames".format(phase))
        arrays={}
        for base in BASES:
            for j in range(WIDTH):
                address=base+j
                xs=[frames[f][address] for f in fs]
                arrays[address]=xs
                counts=Counter(xs)
                run=best=1
                for a,b in zip(xs,xs[1:]):
                    run=run+1 if a==b else 1
                    best=max(best,run)
                transitions=Counter((a,b) for a,b in zip(xs,xs[1:]) if a!=b)
                byte_rows.append(dict(session=session,phase=phase,base="0x{:06X}".format(base),
                    byte_address="0x{:06X}".format(address),byte_index=j,frames=n,
                    unique_values=len(counts),change_rate=rate(xs),
                    top_hex="{:02X}".format(counts.most_common(1)[0][0]),
                    top_fraction=counts.most_common(1)[0][1]/n,
                    longest_constant_run=best,
                    top_transitions=";".join("{:02X}>{:02X}:{}".format(a,b,c)
                                               for (a,b),c in transitions.most_common(5))))
                for lag in LAGS:
                    if lag>=n:continue
                    obs=sum(xs[i]==xs[i-lag] for i in range(lag,n))/(n-lag)
                    independent=sum((v/n)**2 for v in counts.values())
                    period_rows.append(dict(session=session,phase=phase,
                        address="0x{:06X}".format(address),lag=lag,pairs=n-lag,
                        raw_match_rate=obs,independent_match_baseline=independent,
                        excess_match=obs-independent,changed_at_lag_rate=1-obs))
            words=["".join("{:02X}".format(frames[f][base+j]) for j in range(4)) for f in fs]
            count=Counter(words)
            pattern_rows.append(dict(session=session,phase=phase,base="0x{:06X}".format(base),
                frames=n,unique_words=len(count),word_change_rate=rate(words),
                most_common_word=count.most_common(1)[0][0],
                most_common_fraction=count.most_common(1)[0][1]/n,
                alternating_aba_fraction=sum(words[i]==words[i-2] and words[i]!=words[i-1]
                                             for i in range(2,n))/max(1,n-2),
                top_words=top(words)))
            for part,inds in (("high16",(0,1)),("low16",(2,3))):
                for order in ("be","le"):
                    idx=inds if order=="be" else inds[::-1]
                    half=["{:02X}{:02X}".format(frames[f][base+idx[0]],frames[f][base+idx[1]])
                          for f in fs]
                    counts=Counter(half)
                    split_rows.append(dict(session=session,phase=phase,base="0x{:06X}".format(base),
                        part=part,order=order,unique_values=len(counts),
                        change_rate=rate(half),top_hex=counts.most_common(1)[0][0],
                        top_fraction=counts.most_common(1)[0][1]/n))
        for i,left in enumerate(BASES):
            for right in BASES[i+1:]:
                for j in range(4):
                    la,ra=left+j,right+j
                    lx,rx=arrays[la],arrays[ra]
                    changes=[(lx[k]!=lx[k-1],rx[k]!=rx[k-1]) for k in range(1,n)]
                    a=sum(l and r for l,r in changes)
                    b=sum(l and not r for l,r in changes)
                    c=sum(not l and r for l,r in changes)
                    d=sum(not l and not r for l,r in changes)
                    sync_rows.append(dict(session=session,phase=phase,
                        left="0x{:06X}".format(la),right="0x{:06X}".format(ra),
                        frames_compared=n-1,both_changed=a,only_left=b,only_right=c,
                        neither=d,synchrony_given_either=a/(a+b+c) if a+b+c else "",
                        phi=phi(a,b,c,d),value_equal_fraction=sum(x==y for x,y in zip(lx,rx))/n))
    return (byte_rows,split_rows,sync_rows,period_rows,pattern_rows)

OUTPUTS=(
    ("_bytes.csv",BYTE_FIELDS),
    ("_split16.csv",SPLIT_FIELDS),
    ("_synchrony.csv",SYNC_FIELDS),
    ("_periodicity.csv",PERIOD_FIELDS),
    ("_patterns.csv",PATTERN_FIELDS),
)

def run(session,root):
    frames,markers=load(session,root)
    groups=audit(session,frames,markers)
    folder=root/"output"/"csv"
    paths=[folder/("spatial_v2_6_"+session+suffix) for suffix,_ in OUTPUTS]
    if any(p.exists() for p in paths):
        raise FileExistsError("Refusing to overwrite previous v2.6 output")
    for path,(_,fields),rows in zip(paths,OUTPUTS,groups):
        with path.open("x",encoding="utf8",newline="") as output:
            w=csv.DictWriter(output,fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return paths,groups

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--root",type=Path,default=Path("."))
    args=parser.parse_args()
    paths,groups=run(args.session,args.root.resolve())
    for path,rows in zip(paths,groups):
        print("Wrote {} rows={}".format(path,len(rows)))
    print("Raw structure observations only; no coordinate or structure validation.")
