"""Prepare separated generated-file folders; optionally migrate legacy root outputs."""
from pathlib import Path
import argparse
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"output"
DIRS=("csv","sessions","commands","logs","archive")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--migrate",action="store_true",help="Move legacy generated files from repository root")
    args=parser.parse_args()
    for folder in DIRS:
        (OUTPUT/folder).mkdir(parents=True,exist_ok=True)
    if args.migrate:
        for p in ROOT.iterdir():
            if not p.is_file():
                continue
            name=p.name
            if p.suffix.lower()==".csv" and (name.startswith("manual_controls_") or name.startswith("analog_v1_") or name.startswith("autoaim_")):
                target=OUTPUT/"csv"/name
            elif name.endswith("_session.txt") and (name.startswith("manual_controls_") or name.startswith("analog_v1")):
                target=OUTPUT/"sessions"/name
            elif name.endswith("_commands.txt") and name.startswith("manual_controls_"):
                target=OUTPUT/"archive"/name
            else:
                continue
            if target.exists():
                print("SKIP existing:", target.relative_to(ROOT))
                continue
            shutil.move(str(p),str(target))
            print("MOVED",p.name,"=>",target.relative_to(ROOT))
        for p in ROOT.iterdir():
            if p.is_dir() and p.name.endswith("_inbox") and (p.name.startswith("manual_controls_") or p.name.startswith("analog_v1")):
                target=OUTPUT/"commands"/p.name
                if target.exists():
                    print("SKIP existing:",target.relative_to(ROOT))
                else:
                    shutil.move(str(p),str(target))
                    print("MOVED",p.name,"=>",target.relative_to(ROOT))
    print("Output folders ready:",OUTPUT)

if __name__=="__main__":
    main()
