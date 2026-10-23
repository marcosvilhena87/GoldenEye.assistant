"""Export profile default from GoldenEye.mapping (canonical source)."""
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/export_manual_controls_v21.py PATH_TO_MAPPING")
    source = Path(sys.argv[1]) / "catalog" / "manual_controls.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("profile") != "default" or data.get("status") != "operator_confirmed":
        raise SystemExit("Expected operator_confirmed default profile")
    mappings = data.get("mappings", [])
    if not mappings or len({row["button"] for row in mappings}) != len(mappings):
        raise SystemExit("Missing or duplicate buttons")
    q = lambda s: json.dumps(s, ensure_ascii=True)
    lines = ["-- Generated from GoldenEye.mapping; do not hand-edit.",
             "return {profile=" + q(data["profile"]) + ", mappings={"]
    for row in mappings:
        lines.append("  {button=" + q(row["button"]) + ", action_id=" + q(row["action_id"]) + "},")
    lines.append("}}")
    output = Path("config/manual_controls_default.lua")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Exported", output)

if __name__ == "__main__":
    main()
