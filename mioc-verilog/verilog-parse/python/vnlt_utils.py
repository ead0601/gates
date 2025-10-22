# === VNLT REV ===
# file: vnlt_utils.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:util
# note: r2c — shell pipeline support
# === /VNLT REV ===
from registry import CommandRegistry
from expander import convert_output
def execute_line(line:str, interp, reg:CommandRegistry)->str:
 parts=line.strip().split(None,1)
 if not parts: return ''
 cmd=parts[0]; rest=parts[1] if len(parts)>1 else ''
 h=reg.get(cmd)
 if not h: return f"Unknown command '{cmd}'."
 out=h(rest, interp)
 if isinstance(out,dict) and 'fields' in out: return convert_output(out['fields'])
 return '' if out is None else str(out)
