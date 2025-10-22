# === VNLT REV ===
# file: cmds/cmd_exit.py
# rev:  2025-10-20 22:57  r3  tag:cmd
# note: exit — cleanly terminate the REPL by raising SystemExit(0)
# === /VNLT REV ===

from registry import CommandRegistry

def _handler(rest: str, interp) -> str:
    raise SystemExit(0)

def register(reg: CommandRegistry) -> None:
    reg.register("exit", _handler, "Quit the REPL.")
