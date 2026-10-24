"""Enemy Coordinate Discovery v1.6 — three-position temporal screen (candidate-only).
No assumption that moved memory fields are enemy XYZ. Reads raw snapshots only.
"""
import argparse
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path

REGIONS={1:(0x0D5000,0x3500),2:(0x0E6800,0x3500),3:(0x0D3800,0x900)}
WIDTHS=(4,8)
def validate_manifest(rows,root):
    keys={}
    for r in rows:
        if r["notes"]!="same_frame_kseg0_candidate" or r["frame"]!=r["after_frame"] or r["state"]!="ON":
            raise ValueError("Unsafe capture metadata: "+str(r))
        region=int(r["region"]);epoch=int(r["epoch"])
        if region not in REGIONS:raise ValueError("Unknown region")
        phase=r["phase"]
        if phase not in ("stable","hold","camera"):raise ValueError("Unknown phase")
        key=(epoch,phase,region)
        if key in keys:raise ValueError("Duplicate snapshot "+str(key))
        raw=(root/r["file"]).read_bytes()
        if len(raw)!=REGIONS[region][1] or int(r["bytes"])!=len(raw) or int(r["start_hex"],16)!=REGIONS[region][0]:
            raise ValueError("Length/address mismatch for "+str(key))
        keys[key]=raw
    epochs=sorted({e for e,_,_ in keys if (e,"stable",1) in keys})
    if len(epochs)<3:raise ValueError("Need three complete ON epochs")
    epochs=epochs[:3]
    for epoch in epochs:
        for phase in ("stable","hold"):
            for region in REGIONS:
                if (epoch,phase,region) not in keys:
                    raise ValueError("Missing "+str((epoch,phase,region)))
    return keys,epochs

def candidates(keys,epochs,camera_required=False):
    last=epochs[-1]
    cam_present=all((last,"camera",region) in keys for region in REGIONS)
    if camera_required and not cam_present:raise ValueError("Camera control absent")
    result=[]
    summary=Counter()
    for region,(base,size) in REGIONS.items():
        seq=[keys[(e,"stable",region)] for e in epochs]
        holds=[keys[(e,"hold",region)] for e in epochs]
        camera=keys.get((last,"camera",region))
        for width in WIDTHS:
            for off in range(0,size-width+1,width):
                vals=[v[off:off+width] for v in seq]
                hvals=[v[off:off+width] for v in holds]
                stable=all(x==y for x,y in zip(vals,hvals))
                changed12=vals[0]!=vals[1]
                changed23=vals[1]!=vals[2]
                cam_changed=camera is not None and camera[off:off+width]!=vals[2]
                summary[f"region{region}_width{width}_total"]+=1
                summary[f"region{region}_width{width}_stable"]+=int(stable)
                summary[f"region{region}_width{width}_both_transitions"]+=int(changed12 and changed23)
                if not (stable and changed12 and changed23):continue
                summary[f"region{region}_width{width}_eligible"]+=1
                summary[f"region{region}_width{width}_camera_sensitive"]+=int(cam_changed)
                result.append(dict(region=region,offset_hex=f"0x{base+off:06X}",
                    relative_offset=off,field_width=width,
                    stable_hold=1,changed_p1_p2=int(changed12),changed_p2_p3=int(changed23),
                    camera_control_available=int(cam_present),
                    camera_changed=int(cam_changed),
                    p1_hex=vals[0].hex().upper(),p2_hex=vals[1].hex().upper(),
                    p3_hex=vals[2].hex().upper(),
                    status="camera_sensitive" if cam_changed else "temporal_candidate_only"))
    # Identical values at offset in mirrored A and B are one observation, not two.
    indexed={(r["region"],r["relative_offset"],r["field_width"]):r for r in result}
    dedup=[]
    for row in result:
        partner=indexed.get((2,row["relative_offset"],row["field_width"])) if row["region"]==1 else None
        if partner and all(row[k]==partner[k] for k in ("p1_hex","p2_hex","p3_hex")):
            row["mirror_duplicate"]=1
            partner["mirror_duplicate"]=1
        else:row["mirror_duplicate"]=0
    for row in result:
        row.setdefault("mirror_duplicate",0)
        # No numeric/XY claims, prioritize camera-insensitive and nonredundant records.
        if not row["camera_changed"] and not row["mirror_duplicate"]:
            dedup.append(row)
    dedup.sort(key=lambda r:(r["region"],r["relative_offset"],r["field_width"]))
    return result,dedup,dict(summary),cam_present

def run(session,root=Path(".")):
    root=Path(root)
    path=root/"output/csv"/f"enemy_freeze_v1_6_{session}_manifest.csv"
    with path.open(newline="",encoding="utf8") as f:rows=list(csv.DictReader(f))
    keys,epochs=validate_manifest(rows,root)
    raw,selected,counts,cam_present=candidates(keys,epochs)
    base=root/"output/csv"/f"enemy_freeze_v1_6_{session}"
    paths={k:Path(str(base)+"_"+k+".csv") for k in ("temporal_fields","screened_candidates")}
    summary=Path(str(base)+"_analysis.json")
    if any(p.exists() for p in [*paths.values(),summary]):raise FileExistsError("Output exists")
    fields=["region","offset_hex","relative_offset","field_width","stable_hold",
      "changed_p1_p2","changed_p2_p3","camera_control_available","camera_changed",
      "p1_hex","p2_hex","p3_hex","status","mirror_duplicate"]
    for label,data in (("temporal_fields",raw),("screened_candidates",selected)):
        with paths[label].open("x",newline="",encoding="utf8") as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(data)
    report=dict(status="temporal_candidate_only",session=session,epochs=epochs,
       camera_control_available=cam_present,screened_candidates=len(selected),
       temporal_candidates=len(raw),counters=counts,
       caveats=["Camera movement must be manually verified; CAM marker is not sensor ground truth.",
          "Exact byte changes in both intervals do not prove enemy XYZ.",
          "No physical movement vector or enemy identity stored in snapshots.",
          "Mirror and camera filters may have false positives and negatives.",
          "KSEG0 bus mapping and ROM/core still unverified."])
    summary.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("session_id");p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(run(a.session_id,a.root),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
