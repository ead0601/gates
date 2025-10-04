# === VNLT REV ===
# file: python/cmd_ls.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List
from registry import CommandRegistry
from core import Interpreter
from pathlib import Path
import os, time

SUMMARY = "ls [path] — list files in a directory"
DETAIL = """Usage:
  ls [path]

Options:
  -l    Long format (size and modified time)
  -a    Include hidden files (starting with '.')

Examples:
  ls
  ls -l
  ls -la /tmp
"""

def _handler(args: List[str], interp: Interpreter):
    long = False
    allfiles = False
    target = "."
    for a in args:
        if a == "-l":
            long = True
        elif a in ("-a","-A"):
            allfiles = True
        elif a.startswith("-"):
            return {"__raw": DETAIL}
        else:
            target = a
    p = Path(target).expanduser()
    if not p.exists():
        return {"__raw": f"ls: {target}: No such file or directory\n"}
    if p.is_file():
        entries = [p]
    else:
        try:
            entries = sorted(p.iterdir(), key=lambda x: x.name.lower())
        except PermissionError:
            return {"__raw": f"ls: {target}: Permission denied\n"}
    lines = []
    for e in entries:
        name = e.name + ("/" if e.is_dir() else "")
        if not allfiles and name.startswith("."):
            continue
        if long:
            try:
                st = e.stat()
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                size = st.st_size
                lines.append(f"{size:>10}  {mtime}  {name}")
            except Exception:
                lines.append(f"{'?' :>10}  {'-'*19}  {name}")
        else:
            lines.append(name)
    return {"__raw": "\n".join(lines) + ("\n" if lines else "")}

def register(reg: CommandRegistry):
    reg.add_command("ls", _handler, SUMMARY, DETAIL)
