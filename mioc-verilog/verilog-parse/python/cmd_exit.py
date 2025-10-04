# cmd_exit.py
# === VNLT REV ===
# file: python/cmd_exit.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List
from registry import CommandRegistry
from core import Interpreter
from registry import REG as _REG_GLOBAL  # will be None at import time

SUMMARY = "Exit the CLI."
DETAIL = """
Usage:
  exit
  quit
  q

Description:
  Exit the vnlt CLI. Aliases: 'quit', 'q'.
  Returns a special token so the REPL and batch runner terminate cleanly.
"""

def _handler(args: List[str], interp: Interpreter):
    # Any of: exit / quit / q should end the session.
    # The REPL/batch in verilog_parse.py watches for {"cmd": "quit"}.
    return {"cmd": "quit"}

def register(reg: CommandRegistry):
    reg.add_command("exit", _handler, SUMMARY, DETAIL, aliases=["quit", "q"])

# Auto-register if registry.REG is already initialized (defensive)
if _REG_GLOBAL:
    register(_REG_GLOBAL)
