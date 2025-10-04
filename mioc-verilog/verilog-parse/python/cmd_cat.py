# === VNLT REV ===
# file: python/cmd_cat.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List
from registry import CommandRegistry
from core import Interpreter
from pathlib import Path

SUMMARY = "cat <path> — display the contents of a file"
DETAIL = """Usage:
  cat <path>

Notes:
  - Relative paths are resolved from the current working directory of vnlt.
  - Large files will be printed as-is; consider shell redirection (>) to save output.
"""

def _handler(args: List[str], interp: Interpreter):
    if not args:
        return {"__raw": DETAIL}
    path = args[0]
    try:
        p = Path(path).expanduser()
        data = p.read_text(errors="replace")
        # Ensure trailing newline for clean prompt
        return {"__raw": data + ("" if data.endswith("\n") else "\n")}
    except FileNotFoundError:
        return {"__raw": f"cat: {path}: No such file\n"}
    except IsADirectoryError:
        return {"__raw": f"cat: {path}: Is a directory\n"}
    except Exception as e:
        return {"__raw": f"cat: {path}: {e}\n"}

def register(reg: CommandRegistry):
    reg.add_command("cat", _handler, SUMMARY, DETAIL)
