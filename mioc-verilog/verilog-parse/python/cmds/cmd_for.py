# ============================================================================
# File: cmds/cmd_for.py
# REV: r10 — standalone + grouping + quiet-by-default + vnlt→shell split
#        + explicit $(item)/$item substitution per iteration
# One-line loop:
#   for (ITER) do CMD1 ; CMD2 ; ... ; end
# $(item) is set logically per iteration (local substitution), restored by
#   doing nothing globally (no env pollution).
# Clause features:
#   - optional grouping: ( ... )
#   - vnlt command optionally piped to a shell tail and/or > / >> redirect
#   - quote/escape/paren aware splitting like the REPL
# Debug prints are silenced unless VNLT_DEBUG=1 or interp.debug=True.
# ============================================================================

import os, re, subprocess
from pathlib import Path
from registry import CommandRegistry
from expander_runtime import expand_line

# --- debug gate ---------------------------------------------------------------
def _dbg(interp, *args):
    try:
        if getattr(interp, "debug", False) or int(os.getenv("VNLT_DEBUG","0") or "0"):
            print(*args)
    except Exception:
        pass

# --- quote/paren-aware helpers (mirror vnlt splitter logic) ------------------
def _scan_unquoted(s: str, target: str):
    esc=False; q=None; depth=0
    i=0; n=len(s)
    while i<n:
        ch=s[i]
        if esc: esc=False; i+=1; continue
        if ch == '\\':
            esc=True; i+=1; continue
        if q:
            if ch == q: q=None
            i+=1; continue
        if ch in ('"', "'"):
            q=ch; i+=1; continue
        if ch == '(':
            depth += 1; i+=1; continue
        if ch == ')':
            depth = max(0, depth-1); i+=1; continue
        if depth == 0 and ch == target:
            yield i
        i+=1

def _split_pipeline_and_redirect(s: str):
    """Return (vnlt_left, shell_tail, redirect_path, append_flag)"""
    left = s.strip()
    shell_tail = None
    for i in _scan_unquoted(left, '|'):
        shell_tail = left[i+1:].strip()
        left = left[:i].strip()
        break
    gt = list(_scan_unquoted(left, '>'))
    if not gt:
        return left, shell_tail, None, False
    r = gt[-1]
    op_start = r - 1 if r - 1 >= 0 and left[r-1] == '>' else r
    append = (op_start != r)
    j = r + 1
    while j < len(left) and left[j].isspace():
        j += 1
    if j >= len(left):
        return left, shell_tail, None, False
    if left[j] in ('"', "'"):
        q = left[j]; j += 1; k = j
        while k < len(left) and left[k] != q:
            if left[k] == '\\': k += 2; continue
            k += 1
        path = left[j:k]
    else:
        k = j
        while k < len(left) and not left[k].isspace():
            k += 1
        path = left[j:k]
    cmd = left[:op_start].rstrip()
    return cmd, shell_tail, path, append

def _write_redirect(path: str, data: str, append: bool):
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = 'a' if append else 'w'
    with open(p, mode, encoding='utf-8', newline='') as f:
        if data and not data.endswith('\n'):
            f.write(data + '\n')
        else:
            f.write(data)
    return str(p)

def _split_semicolons_top(s: str):
    out, cur = [], []
    q = None
    esc = False
    depth = 0
    for ch in s:
        if esc:
            cur.append(ch); esc = False; continue
        if ch == '\\':
            esc = True; cur.append(ch); continue
        if q:
            if ch == q: q=None
            cur.append(ch); continue
        if ch in ("'", '"'):
            q = ch; cur.append(ch); continue
        if ch == '(':
            depth += 1; cur.append(ch); continue
        if ch == ')':
            depth = max(0, depth-1); cur.append(ch); continue
        if ch == ';' and depth == 0:
            seg = ''.join(cur).strip()
            if seg: out.append(seg)
            cur = []
            continue
        cur.append(ch)
    seg = ''.join(cur).strip()
    if seg: out.append(seg)
    return out

# --- optional clause grouping -------------------------------------------------
def _strip_wrapping_parens(s: str) -> str:
    t = s.strip()
    if not (t.startswith("(") and t.endswith(")")):
        return s
    depth = 0
    esc = False
    q = None
    for i, ch in enumerate(t):
        if esc:
            esc = False; continue
        if ch == '\\':
            esc = True; continue
        if q:
            if ch == q: q = None
            continue
        if ch in ("'", '"'):
            q = ch; continue
        if ch == '(':
            depth += 1; continue
        if ch == ')':
            depth -= 1
            if depth == 0 and i != len(t) - 1:
                return s
    return t[1:-1].strip() if depth == 0 else s

# --- simple text coercion (mirror vnlt) --------------------------------------
def _res_to_text(res):
    if res is None:
        return ''
    if isinstance(res, str):
        return res
    if isinstance(res, dict):
        if '__raw' in res:
            return str(res.get('__raw') or '')
        if 'text' in res:
            return str(res.get('text') or '')
        if 'fields' in res:
            try:
                return ','.join(str(x) for x in (res.get('fields') or []))
            except Exception:
                return '\n'.join(str(x) for x in (res.get('fields') or []))
    return str(res)

# --- core --------------------------------------------------------------------
_ONE_LINE = re.compile(r"^for\s*\((.*?)\)\s*do\s*(.*?)\s*;\s*end\s*$", re.S)

def _materialize_iter_list(iter_expr: str, interp) -> list[str]:
    expanded = expand_line(iter_expr.strip(), interp, interp.registry)
    _dbg(interp, f"for: iter expanded -> {repr(expanded)}")
    if not expanded:
        return []
    if "\n" in expanded and "," not in expanded:
        items = [x.strip() for x in expanded.splitlines() if x.strip()]
    else:
        items = [x.strip() for x in expanded.split(",") if x.strip()]
    _dbg(interp, f"for: items -> {items}")
    return items

def _sub_item(text: str, value: str) -> str:
    # Replace $(item) and $item literally; avoid partial matches.
    # Simple, robust, and quote-friendly for our use.
    return text.replace("$(item)", value).replace("$item", value)

def _run_clause(clause: str, interp, item_val: str) -> str:
    clause0 = clause
    clause = _strip_wrapping_parens(clause.strip())
    if not clause:
        return ""

    # First perform the per-iteration $(item)/$item substitution
    clause = _sub_item(clause, item_val)

    # Split into vnlt_left | shell_tail and optional redirection
    vnlt_left, shell_tail, out_path, append = _split_pipeline_and_redirect(clause)
    _dbg(interp, f"for: clause split: left={repr(vnlt_left)} shell={repr(shell_tail)} out={repr(out_path)} append={append}")

    # Expand & run the vnlt side first ($..., #( ), %( ) apply now)
    vnlt_expanded = expand_line(vnlt_left, interp, interp.registry)
    _dbg(interp, f"for: vnlt_expanded={repr(vnlt_expanded)}")
    try:
        res = interp.registry.dispatch(vnlt_expanded, interp)
    except SystemExit:
        raise
    except Exception as e:
        _dbg(interp, f"for: dispatch error {e}")
        res = ""

    text = _res_to_text(res)

    # If there is a shell tail, substitute $(item)/$item in it too (rare but safe)
    if shell_tail:
        shell_tail = _sub_item(shell_tail, item_val)
        _dbg(interp, f"for: running shell tail: {shell_tail}")
        p = subprocess.Popen(['/bin/sh','-c', shell_tail],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(text)
        if err and err.strip():
            # Only print shell errors in debug
            _dbg(interp, f"[SHELL ERROR {p.returncode}] {err.strip()}")
        text = out

    # Handle redirect if present
    if out_path:
        _write_redirect(out_path, text, append)
        return ""

    return text

def _handler(rest: str, interp) -> str:
    r = rest.strip()
    line = r if r.startswith("for ") else f"for {r}"
    _dbg(interp, f"for: handler line={repr(line)}")
    m = _ONE_LINE.match(line)
    if not m:
        print("for: one-line form must end with '; end'")
        return ""

    iter_expr, body = m.groups()
    _dbg(interp, f"for: iter_expr={repr(iter_expr)} body={repr(body)}")

    items = _materialize_iter_list(iter_expr, interp)
    if not items:
        _dbg(interp, "for: no items -> exit")
        return ""

    clauses = _split_semicolons_top(body)
    _dbg(interp, f"for: clauses -> {clauses}")
    if not clauses:
        _dbg(interp, "for: no clauses -> exit")
        return ""

    out_lines = []
    for it in items:
        _dbg(interp, f"for: iteration item={repr(it)}")
        for clause in clauses:
            out = _run_clause(clause, interp, it)
            if out:
                out_lines.append(out)

    return "\n".join(s for s in out_lines if s)

# --- registration -------------------------------------------------------------
def register(reg: CommandRegistry):
    reg.register(
        "for",
        _handler,
        "for (ITER) do CMD1 ; ... ; end  — one-line loop; $(item) set per iteration.",
    )
