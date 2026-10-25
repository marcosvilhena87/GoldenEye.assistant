"""Compare separate v1.8.13 sessions using relative response metrics, not absolute addresses."""
import argparse,json
from pathlib import Path
def compare(a,b):
 if a["protocol"]!="bond_position_candidate_validation_v1_8_13" or b["protocol"]!=a["protocol"]:
  raise ValueError("incompatible protocol")
 if a["session"]==b["session"]:raise ValueError("two independent sessions required")
 rows=[]
 for left,right in zip(a["results"],b["results"]):
  if left["bond_pair"]!=right["bond_pair"]:raise ValueError("different candidates")
  rows.append({"bond_pair":left["bond_pair"],
    "session_a_return_error":left["return_error_by_phase"]["RETURN_STILL"],
    "session_b_return_error":right["return_error_by_phase"]["RETURN_STILL"],
    "session_a_max_still_spread":left["max_still_numeric_spread"],
    "session_b_max_still_spread":right["max_still_numeric_spread"],
    "both_completed":a["capture_complete"] and b["capture_complete"],
    "cross_save_validation":False})
 return {"protocol":"bond_position_v1_8_13_cross_session","sessions":[a["session"],b["session"]],
         "results":rows,"same_save_or_rom_confirmed":False,"cross_save_validated":False,
         "note":"Sessions may be within the same save; verify independently. Similar metrics alone do not prove layout persistence."}
def main():
 p=argparse.ArgumentParser();p.add_argument("report_a",type=Path);p.add_argument("report_b",type=Path)
 a=p.parse_args()
 result=compare(json.loads(a.report_a.read_text(encoding="utf-8")),json.loads(a.report_b.read_text(encoding="utf-8")))
 print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
