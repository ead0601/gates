# REV:r1
# repl_capture.py — capture final textual stdout from executing a vnlt line

import io
import sys
try:
    from verilog_parse import _exec_core as _repl_exec_one_line
except Exception:
    _repl_exec_one_line = None

def capture_text(line: str, interp, reg) -> str:
    if _repl_exec_one_line is None:
        return ""
    cap_out = io.StringIO()
    cap_err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = cap_out, cap_err
        res = _repl_exec_one_line(line, interp, reg)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    out = cap_out.getvalue()
    if out:
        return out
    if isinstance(res, str):
        return res
    if isinstance(res, (tuple, list)) and res and isinstance(res[0], str):
        return res[0]
    if isinstance(res, dict) and "__raw" in res and isinstance(res["__raw"], str):
        return res["__raw"]
    return ""
