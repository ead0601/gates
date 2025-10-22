# === VNLT REV ===
# file: cmds/cmd_set.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:cmd
# note: r2c — shell pipeline support
# === /VNLT REV ===
from registry import CommandRegistry
import variables as VARS
def _handler(rest:str, interp)->str:
 if '=' not in rest: return "Usage: set name=a,b,c"
 name,vals=rest.split('=',1); name=name.strip()
 values=[p.strip() for p in vals.split(',') if p.strip()]
 VARS.setv(name, values)
 return f"set {name} -> {','.join(VARS.getv(name))}"
def register(reg: CommandRegistry): reg.register('set', _handler, 'define variable for $name/$(name)')
