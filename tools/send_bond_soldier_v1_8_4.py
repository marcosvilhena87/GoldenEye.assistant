"""Safe command sender for Bond-Soldier v1.8.4; never writes game memory."""
from pathlib import Path
import argparse
import os
import tempfile

VALID = {"BASELINE", "FREEZE_ON", "FREEZE_OFF", "CAMERA_ONLY",
         "BOND_MOVE", "SOLDIER_MOVE", "WRITE_PRE", "WRITE_APPLIED",
         "WRITE_OBSERVE", "STOP", "SOLDIER_STILL", "SOLDIER_MOVING", "SOLDIER_REFROZEN", "FREEZE_REQUEST_ON", "FREEZE_REQUEST_OFF", "VISUAL_STILL", "VISUAL_MOVING"}

def send(label, root=None):
    if label not in VALID:
        raise ValueError("Invalid label: " + label)
    base = Path(root) if root is not None else Path(__file__).resolve().parent.parent / "output"
    sid = (base / "sessions" / "bond_soldier_v1_8_4_session.txt").read_text(encoding="utf-8").strip()
    if not sid or any(c in sid for c in "/\\\r\n") or ".." in sid:
        raise ValueError("Invalid SID")
    commands = base / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    # Construct the complete command in an invisible temporary file first.
    # Publishing via rename prevents Lua from observing an empty/partial file.
    fd, temp_name = tempfile.mkstemp(prefix=".bond_soldier_v1_8_4_", suffix=".tmp", dir=commands)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as out:
            out.write(f"LABEL:{label}\n")
            out.flush()
            os.fsync(out.fileno())
        for seq in range(1, 10000):
            path = commands / f"bond_soldier_v1_8_4_{sid}_{seq:04d}.txt"
            if path.exists():
                continue
            try:
                # On Windows os.rename fails if destination already exists.
                os.rename(temp, path)
                return path
            except FileExistsError:
                continue
    finally:
        if temp.exists():
            temp.unlink()
    raise RuntimeError("Command limit exceeded")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", choices=sorted(VALID))
    parser.add_argument("--root", type=Path, default=None, help="Output directory, defaults to repository/output")
    args = parser.parse_args()
    path = send(args.label, args.root)
    print("Created", path, "; await MARKED confirmation in BizHawk before next command")

if __name__ == "__main__":
    main()
