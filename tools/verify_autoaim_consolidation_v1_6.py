"""Check the canonical experiment record; never export candidate offsets as executable symbols."""
import argparse,json
from pathlib import Path
REQUIRED={"0x040A93","0x0D308B","0x0D309B","0x067D37","0x069AAD"}
def verify(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("status")!="experimentally_reproduced" or data.get("operational_permission")!="none" or data.get("rom_identity_verified") is not False:
        raise ValueError("unsafe experimental metadata")
    entries=data.get("candidate_offsets",[])
    offsets=[entry.get("offset_hex") for entry in entries]
    if len(offsets)!=5 or set(offsets)!=REQUIRED:raise ValueError("candidate offset mismatch")
    statuses={e["offset_hex"]:e.get("status") for e in entries}
    if any(statuses[k]!="experimentally_reproduced" for k in ("0x040A93","0x0D308B","0x0D309B")):raise ValueError("reproduction status mismatch")
    if any(statuses[k]!="needs_validation" for k in ("0x067D37","0x069AAD")):raise ValueError("secondary status mismatch")
    sessions={e["session"]:e for e in data.get("evidence_sessions",[])}
    controlled=sessions.get("20261023T213220Z_234487")
    if not controlled or len(controlled.get("frames",[]))!=6:raise ValueError("six controlled interventions required")
    controls=sessions.get("20261023T215226Z_301601")
    if not controls:raise ValueError("negative control provenance missing")
    if data.get("summary",{}).get("principal_offset_transitions_in_controls")!=0:raise ValueError("negative control mismatch")
    return {"status":data["status"],"candidate_count":len(offsets),"controlled_events":6,"operational_permission":"none"}
def main():
    p=argparse.ArgumentParser();p.add_argument("mapping",type=Path);args=p.parse_args()
    record=args.mapping/"experiments/autoaim_semantic_consolidation_v1_6_20261023.json"
    print("v1.6 read-only evidence check:",verify(record))
if __name__=="__main__":main()
