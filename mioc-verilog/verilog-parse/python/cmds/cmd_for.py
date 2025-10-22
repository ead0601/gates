# === VNLT REV ===
# file: cmds/cmd_for.py
# rev:  2025-10-22 00:22  r6  by:Drater  tag:cmd
# note: Safe import: no top-level vnlt imports. One-line loop; $item per-iteration; allow_loop_vars used in body only.
# === /VNLT REV ===

from typing import List, Tuple
import re

from registry import CommandRegistry
from variables import setv as _setv
from expander_runtime import get_executor as _get_exec

# Defer vnlt imports until inside handler to avoid any circulars.
_fmt_result = None

def _fallback_to_text(res) -> str:
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
            vals = res.get('fields') or []
            try:
                return ','.join(str(x) for x in vals)
            except Exception:
                return '\n'.join(str(x) for x in vals)
    return str(res)

def _to_text(res) -> str:
    global _fmt_result
    if _fmt_result is None:
        try:
            from vnlt import _res_to_text as _rt
            _fmt_result = _rt
        except Exception:
            _fmt_result = False
    if _fmt_result and _fmt_result is not False:
        try:
            tmp = _fmt_result(res)
            return tmp if isinstance(tmp, str) else _fallback_to_text(tmp)
        except Exception:
            pass
    return _fallback_to_text(res)

def _find_matching_paren(s: str, start_idx: int) -> int:
    i = start_idx + 1
    depth = 1
    q = None
    esc = False
    n = len(s)
    while i < n:
        ch = s[i]
        if esc:
            esc = False; i += 1; continue
        if ch == '\\':
            esc = True; i += 1; continue
        if q:
            if ch == q:
                q = None
            i += 1; continue
        if ch in ('"', "'"):
            q = ch; i += 1; continue
        if ch == '(':
            depth += 1; i += 1; continue
        if ch == ')':
            depth -= 1
            if depth == 0:
                return i
            i += 1; continue
        i += 1
    return -1

def _split_semicolons_top(s: str) -> List[str]:
    out: List[str] = []
    i = 0
    start = 0
    q = None
    esc = False
    depth = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if esc:
            esc = False; i += 1; continue
        if ch == '\\':
            esc = True; i += 1; continue
        if q:
            if ch == q:
                q = None
            i += 1; continue
        if ch in ('"', "'"):
            q = ch; i += 1; continue
        if ch == '(':
            depth += 1; i += 1; continue
        if ch == ')':
            if depth > 0: depth -= 1
            i += 1; continue
        if ch == ';' and depth == 0:
            frag = s[start:i].strip()
            if frag:
                out.append(frag)
            start = i + 1
            i += 1; continue
        i += 1
    tail = s[start:].strip()
    if tail:
        out.append(tail)
    return out

_var_pat = re.compile(r'^\s*\$(?:\((?P<n1>[A-Za-z_][A-Za-z0-9_]*)\)|(?P<n2>[A-Za-z_][A-Za-z0-9_]*))\s*$')

def _iter_from_expr(expr: str, interp, reg) -> List[str]:
    s = (expr or '').strip()
    if not s:
        return []

    if (s.startswith('#(') or s.startswith('%(')) and s.endswith(')'):
        op = s[0]
        inner = s[2:-1]
        exec_vnlt = _get_exec(reg, interp)
        text = exec_vnlt(inner.strip())
        if op == '#':
            parts = [p.strip() for p in text.split(',')]
        else:
            parts = [p.strip() for p in re.split(r'\r?\n', text)]
        return [p for p in parts if p]

    m = _var_pat.match(s)
    if m:
        name = m.group('n1') or m.group('n2')
        vals = []
        if hasattr(interp, 'variables') and isinstance(interp.variables, dict):
            raw = interp.variables.get(name)
            if isinstance(raw, (list, tuple)):
                vals = [str(v) for v in raw]
            elif isinstance(raw, str):
                vals = [v.strip() for v in raw.split(',') if v.strip()]
        if not vals:
            try:
                from variables import getv as _getv
                vals = _getv(name)
            except Exception:
                vals = []
        return [str(v).strip() for v in vals if str(v).strip()]

    parts = [p.strip() for p in s.split(',')]
    return [p for p in parts if p]

def _parse_one_line_for(rest: str) -> Tuple[str, str]:
    t = (rest or '').strip()
    if not t or t[0] != '(':
        raise ValueError("usage: for (ITER) do CMD1 ; ... ; end")
    r = _find_matching_paren(t, 0)
    if r < 0:
        raise ValueError("for: unmatched '(' in ITER")
    iter_expr = t[1:r]
    after = t[r+1:].lstrip()
    if not after.lower().startswith('do'):
        raise ValueError("for: expected 'do' after (ITER)")
    body = after[2:].strip()
    if not body.lower().endswith('end'):
        raise ValueError("for: one-line form must end with '; end'")
    body_wo_end = body[:-3].rstrip()
    if not body_wo_end.endswith(';'):
        raise ValueError("for: missing ';' before end")
    body_wo_end = body_wo_end[:-1].rstrip()
    if not body_wo_end:
        raise ValueError("for: empty body")
    return iter_expr, body_wo_end

def _ensure_interp_vars(interp):
    if not hasattr(interp, 'variables') or not isinstance(interp.variables, dict):
        try:
            interp.variables = {}
        except Exception:
            pass

def _bind_item(interp, value: str):
    _ensure_interp_vars(interp)
    try:
        interp.variables['item'] = str(value)
    except Exception:
        pass
    _setv('item', [value])

# @help for
# for (ITER) do CMD1 ; ... ; end
# Iterate over ITER and run the body per item. The loop variable is $(item).
# Examples:
#   set nets=A,B,C
#   for ($nets)  do echo $(item) ; end
#   for (A,B)    do echo X$(item)X ; end
#   for (A,B)    do echo $(item) >> out.txt ; end
#
# @manual for
# Goal:
#   Iterate a list and execute one or more VNLT body clauses per item.
# Iterator sources:
#   - $name or $(name): if list, iterate; if string, split on commas.
#   - #( vnlt ): run vnlt, split result on commas.
#   - %( vnlt ): run vnlt, split result on newlines.
#   - Literal: split on commas.
# Body:
#   One or more VNLT commands separated by ';'. Each clause may pipe to shell
#   or redirect (> / >>) per iteration.
# Outputs:
#   Aggregated text from clauses that did not redirect/pipe.
# Notes:
#   - Loop var $(item) is set per iteration and left as the final value after the loop.
#   - Empty iterator: no iterations, no error.
#   - Clause errors: continue to next item.

def _handler(rest: str, interp) -> str:
    try:
        iter_expr, body = _parse_one_line_for(rest)
    except Exception as e:
        return str(e)

    items = _iter_from_expr(iter_expr, interp, interp.registry)
    if not items:
        return f"[for] no items from ITER: ({iter_expr.strip()})"

    clauses = _split_semicolons_top(body)
    if not clauses:
        return ''

    outputs: List[str] = []
    try:
        from vnlt import _dispatch_one as _dispatch_one_vnlt
    except Exception as e:
        return f"[for] internal import error: {e}"

    old_flag = getattr(interp, 'allow_loop_vars', False)
    try:
        for it in items:
            _bind_item(interp, it)
            try:
                interp.allow_loop_vars = True
            except Exception:
                pass
            for clause in clauses:
                cut = clause.strip()
                if not cut:
                    continue
                try:
                    res = _dispatch_one_vnlt(interp.registry, interp, cut)
                    txt = _to_text(res)
                except SystemExit:
                    txt = ''
                except Exception as e:
                    txt = f"[for] error: {e}"
                if txt:
                    outputs.append(txt.rstrip())
    finally:
        try:
            interp.allow_loop_vars = old_flag
        except Exception:
            pass

    return "\n".join(outputs)

def register(reg: CommandRegistry) -> None:
    reg.register("for", _handler, "for (ITER) do CMD1 ; ... ; end  — one-line loop; $item set per iteration.")
