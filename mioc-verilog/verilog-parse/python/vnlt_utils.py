# === VNLT REV ===
# file: vnlt_utils.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:util
# note: r2c — shell pipeline support
#       r2c+dbg — add dbg() helper guarded by interp.debug or env VNLT_DEBUG.
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

# --- debug helper ---
import os

def dbg(interp, prefix: str, msg: str, *args):
    """Guarded debug print. Uses interp.debug or VNLT_DEBUG env var."""
    enabled = getattr(interp, 'debug', None)
    if enabled is None:
        try:
            enabled = bool(int(os.getenv('VNLT_DEBUG', '0') or '0'))
        except Exception:
            enabled = False
    if not enabled:
        return
    try:
        text = msg % args if args else str(msg)
    except Exception:
        text = f"{msg} | args={args}"
    print(f"{prefix}: {text}")
