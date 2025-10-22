# === VNLT REV ===
# file: cmds/cmd_vars.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:cmd
# note: r2c — shell pipeline support
# === /VNLT REV ===
from registry import CommandRegistry
import variables as VARS
def _handler(rest:str, interp)->str:
 lines=[f"{k}={','.join(v)}" for k,v in VARS.all_items()]
 return "\n".join(lines) if lines else "(no variables)"
def register(reg: CommandRegistry): reg.register('vars', _handler, 'List variables')
