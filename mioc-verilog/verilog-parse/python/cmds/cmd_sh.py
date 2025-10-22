# === VNLT REV ===
# file: cmds/cmd_sh.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:cmd
# note: r2c — shell pipeline support
# === /VNLT REV ===
from registry import CommandRegistry
from shell_util import run_shell
def _handler(rest:str, interp)->str:
 script=rest.strip()
 if not script: return ""
 out,rc,err=run_shell(script,"")
 if rc!=0 and not out: return f"[SHELL ERROR {rc}] {err.strip()}"
 return out
def register(reg: CommandRegistry): reg.register('sh', _handler, 'sh CMD — execute CMD in /bin/sh')
