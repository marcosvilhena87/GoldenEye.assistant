"""Bond Heading v1.9.10: lag/correlation analysis for historical raw pitch probes.

Uses existing v1.9.8 or v1.9.9 samples. Does not touch BizHawk memory.
"""
import argparse,csv,json,math,re
from pathlib import Path
from tools.audit_bond_heading_hud_v1_9_9 import audit as temporal_audit

NAMES=("0D3998","0D3D40","0D39A0","0D3D48")
PAIRS=(("0D3998","0D3D40"),("0D39A0","0D3D48"),("0D3998","0D39A0"))
VERTICAL=("CAMERA_PITCH_UP","CAMERA_PITCH_DOWN","AIM_MODE_PITCH_UP","AIM_MODE_PITCH_DOWN")
def pearson(xs,ys):
 if len(xs)<3:return None
 mx=sum(xs)/len(xs);my=sum(ys)/len(ys)
 xx=sum((x-mx)**2 for x in xs);yy=sum((y-my)**2 for y in ys)
 if xx<1e-15 or yy<1e-15:return None
 return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(xx*yy)
def shifted(a,b,lag):
 """Compare a[t] to b[t+lag]; positive lag means b occurs later."""
 if lag>=0:return a[:len(a)-lag or None],b[lag:]
 lag=-lag
 return a[lag:],b[:len(b)-lag or None]
def lag_scan(a,b,maxlag=120,minimum=8):
 """Demeaned per-frame differences; excludes missing and nonfinite values."""
 da=[a[i]-a[i-1] if a[i] is not None and a[i-1] is not None else None for i in range(1,len(a))]
 db=[b[i]-b[i-1] if b[i] is not None and b[i-1] is not None else None for i in range(1,len(b))]
 candidates=[]
 for lag in range(-maxlag,maxlag+1):
  x,y=shifted(da,db,lag)
  valid=[(u,v) for u,v in zip(x,y) if u is not None and v is not None]
  if len(valid)<minimum:continue
  corr=pearson([u for u,v in valid],[v for u,v in valid])
  if corr is not None:candidates.append({"lag_frames":lag,"pearson":corr,"samples":len(valid)})
 if not candidates:return {"best":None,"zero_lag":None,"tested_lags":0}
 best=max(candidates,key=lambda o:(abs(o["pearson"]),-abs(o["lag_frames"])))
 zero=next((c for c in candidates if c["lag_frames"]==0),None)
 return {"best":best,"zero_lag":zero,"tested_lags":len(candidates)}
def read_samples(p):
 with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def audit(sid,root=Path("output/csv"),version="v1_9_8",maxlag=120):
 if not re.fullmatch(r"[A-Za-z0-9_]+",sid):raise ValueError("invalid SID")
 if version not in ("v1_9_8","v1_9_9","v1_9_10"):raise ValueError("invalid source version")
 base=root/f"bond_heading_hud_{version}_{sid}"
 rows=read_samples(Path(str(base)+"_samples.csv"))
 if not rows:raise ValueError("empty source")
 if any(r["session"]!=sid for r in rows):raise ValueError("mixed SID")
 segments=[]
 for row in rows:
  if not segments or segments[-1]["phase"]!=row["phase"]:
   segments.append({"phase":row["phase"],"rows":[]})
  segments[-1]["rows"].append(row)
 output=[]
 for i,segment in enumerate(segments):
  block=segment["rows"]
  signals={}
  for n in NAMES:
   values=[]
   for row in block:
    try:
     x=float(row["auxf_"+n]);values.append(x if math.isfinite(x) else None)
    except (ValueError,TypeError,KeyError):values.append(None)
   signals[n]=values
  pairresults={}
  for a,b in PAIRS:
   exact=sum(row["aux_"+a]==row["aux_"+b] for row in block)
   scan=lag_scan(signals[a],signals[b],min(maxlag,max(0,len(block)-2)))
   pairresults[a+"_"+b]={"raw_equal_fraction":exact/len(block),"raw_equal_frames":exact,
    "lag_scan":scan}
  output.append({"index":i,"phase":segment["phase"],"frames":len(block),
    "start_frame":int(block[0]["frame"]),"end_frame":int(block[-1]["frame"]),
    "pairs":pairresults})
 report={"version":"v1.9.10","source_version":version,"sid":sid,
  "source_frames":len(rows),"lag_sign":"positive lag means second signal changes later",
  "max_lag_frames":maxlag,"vertical_interventions":[r for r in output if r["phase"] in VERTICAL],
  "segments":output,
  "historical_complete":None,
  "pitch_confirmed":False,"reticle_confirmed":False,
  "limitations":["Correlation and lag are not evidence of causality or physical pitch units.",
  "Flat signals return undefined Pearson correlation; this is not a zero relationship.",
  "Searches multiple lags: selected maximum |r| can be inflated; confirm in fresh captures.",
  "Operator-labeled segments do not certify exact time of controller activation."]}
 if version in ("v1_9_8","v1_9_9"):
  report["historical_complete"]=temporal_audit(sid,root,version)["complete"]
 return report
def main():
 p=argparse.ArgumentParser()
 p.add_argument("sid");p.add_argument("--root",type=Path,default=Path("output/csv"))
 p.add_argument("--source-version",choices=["v1_9_8","v1_9_9"],default="v1_9_8")
 p.add_argument("--max-lag",type=int,default=120)
 a=p.parse_args()
 if not 0<=a.max_lag<=2000:p.error("max-lag must be 0..2000")
 report=audit(a.sid,a.root,a.source_version,a.max_lag)
 dest=a.root/f"bond_heading_hud_v1_9_10_{a.sid}_correlation.json"
 if dest.exists():raise FileExistsError(dest)
 dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"v1.9.10 correlation: {dest} frames={report['source_frames']} complete={report['historical_complete']}")
if __name__=="__main__":main()
