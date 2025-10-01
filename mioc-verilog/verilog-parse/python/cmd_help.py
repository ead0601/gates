from typing import List, Optional
from registry import CommandRegistry
from core import Interpreter
from registry import REG as _REG_GLOBAL  # will be None at import time

def _handler(args: List[str], interp: Interpreter):
    from registry import REG
    reg: CommandRegistry = REG  # type: ignore
    if not args:
        lines = ["Commands:"]
        for name, summary in reg.list_commands().items():
            lines.append(f"  {name:16s} {summary}")
        lines.append("")
        return {"__raw": "\n".join(lines)}
    topic = args[0]
    detail = reg.help_detail(topic)
    if detail:
        return {"__raw": detail}
    return {"__raw": f"No detailed help for '{topic}'.\n"}

SUMMARY = "help [cmd] — show list or details"
DETAIL = """\
Usage:
  help [cmd]
  ? [cmd]

Description:
  Show top-level help or details for a specific command.
"""

def register(reg: CommandRegistry):
    reg.add_command("help", _handler, SUMMARY, DETAIL, aliases=["?"])

# auto-register if registry.REG is already initialized (defensive)
if _REG_GLOBAL:
    register(_REG_GLOBAL)
