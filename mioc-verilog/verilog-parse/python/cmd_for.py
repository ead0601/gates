# REV:r4
# cmd_for.py — bash-like one-line loop over items and run a vnlt command per item
#
# Usage:
#   for VAR in <items...> [--echo] [--limit N] do <vnlt-line-using-$VAR> end
#   for VAR in $( <vnlt-line> ) [--echo] [--limit N] do <vnlt-line-using-$VAR> end
#
import re, shlex, io, sys
import var_store as _vs
try:
    from verilog_parse import _exec_core as _repl_exec_one_line
except Exception:
    _repl_exec_one_line = None

_VALID = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def _expand_store_vars(text: str, exclude: set | None = None) -> str:
    """Expand $name and ${name} from var_store, skipping any names in exclude."""
    exclude = exclude or set()
    def rb(m):
        name = m.group(1)
        if name in exclude:
            return m.group(0)
        return ' '.join(_vs.get(name))
    def rs(m):
        name = m.group(1)
        if name in exclude:
            return m.group(0)
        return ' '.join(_vs.get(name))
    text = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', rb, text)
    text = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)\b', rs, text)
    return text

def _expand_loop_var(text: str, var: str, value: str) -> str:
    text = re.sub(r'\$\{' + re.escape(var) + r'\}', value, text)
    text = re.sub(r'\$' + re.escape(var) + r'\b', value, text)
    return text

def _compose_result_from_exec(line: str, interp, reg) -> str:
    """Capture prints + returns; for strings, append RAW text (not repr)."""
    cap_out = io.StringIO(); cap_err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = cap_out, cap_err
        res = _repl_exec_one_line(line, interp, reg)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    buf = []
    so, se = cap_out.getvalue(), cap_err.getvalue()
    if so: buf.append(so)
    if se: buf.append(se)
    if res is not None:
        if isinstance(res, str):
            if res:
                buf.append(res if res.endswith('\n') else res + '\n')
        else:
            buf.append(repr(res) + '\n')
    return ''.join(buf)

def register(reg):
    def _for(args, interp=None):
        if _repl_exec_one_line is None:
            return "for: internal error: REPL single-line executor not available"
        if not args:
            return "for: usage: for VAR in <items...> [--echo] [--limit N] do <line> end"
        spec = " ".join(args)
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.*?)\s+do\s+(.*)\s+end\s*$', spec)
        if not m:
            return "for: syntax error. Use: for VAR in <items...> [--echo] [--limit N] do <line> end"
        var = m.group(1)
        if not _VALID.match(var):
            return "for: invalid loop var name"
        head = m.group(2).strip()
        body = m.group(3)
        items = []; echo = False; limit = None
        # Head: expand store vars normally (global $(...) already expanded pre-dispatch)
        head_expanded = _expand_store_vars(head)
        head_toks = shlex.split(head_expanded, posix=True)
        i = 0
        while i < len(head_toks):
            t = head_toks[i]
            if t == '--echo':
                echo = True; i += 1; continue
            if t == '--limit' and i + 1 < len(head_toks):
                try: limit = int(head_toks[i+1])
                except ValueError: return "for: --limit requires an integer"
                i += 2; continue
            items.append(t); i += 1
        if limit is not None and limit >= 0:
            items = items[:limit]
        # Body: expand store vars but DO NOT touch the loop var; then substitute the loop var.
        body_expanded_store = _expand_store_vars(body, exclude={var})
        out_parts = []
        for item in items:
            line = _expand_loop_var(body_expanded_store, var, item)
            if echo: out_parts.append(line + '\n')
            out_parts.append(_compose_result_from_exec(line, interp, reg))
        return "".join(out_parts)

    reg.add_command("for", _for, "for VAR in <items...> [--echo] [--limit N] do <line> end — loop and run a command per item")
