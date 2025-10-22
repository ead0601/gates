# === VNLT REV ===
# file: cmds/cmd_echo.py
# rev:  2025-10-21 01:11  r3  tag:cmd
# note: echo — return plain text only (no dict). Works in REPL and source identically.
# === /VNLT REV ===

from registry import CommandRegistry

def _handler(rest: str, interp) -> str:
    # 'rest' is already post-expansion by vnlt core; echo should not reinterpret it.
    if rest is None:
        return ""
    # Avoid echoing stray leading space if dispatcher split on first space
    s = rest[1:] if rest.startswith(" ") else rest
    return s

def register(reg: CommandRegistry) -> None:
    reg.register("echo", _handler, "echo args — expands $var, #(cmd)->list, %(cmd)->lines")
