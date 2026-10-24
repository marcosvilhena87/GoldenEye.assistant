"""Spatial v2.2: frequency-controlled periodicity diagnostics, offline v1.9 data."""
import argparse,csv,math,random
from collections import Counter
from pathlib import Path
try:
 from tools.analyze_spatial_position_v2_0 import validate,ADDRS,PHASES
except ModuleNotFoundError:
 from analyze_spatial_position_v2_0 import validate,ADDRS,PHASES

HEADER=("session","phase","address","lag","pairs","raw_match_rate","iid_expected_match",
        "excess_match","change_agreement","iid_expected_change_agreement",
        "excess_change_agreement","permutation_p","null_mean","null_q95","candidate_only")
def score(values,lag):
 n=len(values)-lag
 match=sum(values[i]==values[i-lag] for i in range(lag,len(values)))/n
 changes=[values[i]!=values[i-1] for i in range(1,len(values))]
 agree=sum(changes[i]==changes[i-lag] for i in range(lag,len(changes)))/max(1,len(changes)-lag)
 return match,agree

def examine(session,data,marks,max_lag=32,permutations=199,seed=220):
 if max_lag<1 or max_lag>1024 or permutations<20 or permutations>9999:raise ValueError("Invalid limits")
 rnd=random.Random(seed)
 rows=[]
 for index,phase in enumerate(PHASES):
  frames=range(marks[index],marks[index+1])
  for addr in ADDRS:
   values=[data[f][addr] for f in frames]
   # Bound expensive permutation tests to a deterministic prefix; all reported\n   # statistics for a lag use the exact same subset.\n   values=values[:min(len(values),512)]\n   n=len(values)\n   if n<max_lag+3:raise ValueError("Phase too short")
   counts=Counter(values)
   expected=sum((v/n)**2 for v in counts.values())
   changes=[values[i]!=values[i-1] for i in range(1,n)]
   q=sum(changes)/len(changes)
   expected_agree=q*q+(1-q)*(1-q)
   for lag in range(1,max_lag+1):
    observed,agree=score(values,lag)
    null=[]
    for _ in range(permutations):
     shuffled=values.copy()
     rnd.shuffle(shuffled)
     null.append(score(shuffled,lag)[0])
    null.sort()
    p=(1+sum(x>=observed for x in null))/(permutations+1)
    rows.append(dict(session=session,phase=phase,address=addr,lag=lag,pairs=n-lag,
     raw_match_rate=observed,iid_expected_match=expected,excess_match=observed-expected,
     change_agreement=agree,iid_expected_change_agreement=expected_agree,
     excess_change_agreement=agree-expected_agree,permutation_p=p,
     null_mean=sum(null)/len(null),null_q95=null[min(len(null)-1,math.ceil(.95*len(null))-1)],
     candidate_only=True))
 return rows

def run(session,root,max_lag=32,permutations=199,seed=220):
 data,marks=validate(session,root)
 rows=examine(session,data,marks,max_lag,permutations,seed)
 dest=root/"output/csv"/("spatial_v2_2_"+session+"_periodicity.csv")
 with dest.open("x",encoding="utf8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=HEADER);writer.writeheader();writer.writerows(rows)
 return dest,rows

def main():
 p=argparse.ArgumentParser()
 p.add_argument("session");p.add_argument("--root",type=Path,default=Path("."))
 p.add_argument("--max-lag",type=int,default=32)
 p.add_argument("--permutations",type=int,default=199)
 p.add_argument("--seed",type=int,default=220)
 a=p.parse_args()
 dest,rows=run(a.session,a.root.resolve(),a.max_lag,a.permutations,a.seed)
 print("Wrote",dest,"rows="+str(len(rows)))
 print("Null shuffles are descriptive only; correlated data and multiple testing limit significance.")
if __name__=="__main__":main()
