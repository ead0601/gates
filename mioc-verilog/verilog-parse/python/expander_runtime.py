# === VNLT REV ===
# file: expander_runtime.py
# rev:  2025-10-21 01:54  r5  tag:exp
# note: Add plain $name / $(name) interpolation outside of %(...) and #(...). Keep special handling inside fields.
# === /VNLT REV ===

from typing import List, Tuple
import re

try:
    from vnlt import _res_to_text as _fmt_result
except Exception:
    _fmt_result = None

def _to_text(res) -> str:
    if _fmt_result:
        try:
            t = _fmt_result(res)
            return t if isinstance(t, str) else str(t)
        except Exception:
            pass
    if res is None:
        return ''
    if isinstance(res, dict):
        if '__raw' in res: return str(res.get('__raw') or '')
        if 'text' in res:  return str(res.get('text') or '')
        if 'fields' in res:
            vals = res.get('fields') or []
            try:    return ','.join(str(x) for x in vals)
            except: return '\n'.join(str(x) for x in vals)
    return str(res)

def _get_var_vals(name: str, interp) -> List[str]:
    try:
        import variables as _vars
        vals = _vars.getv(name)
        if isinstance(vals, list):
            return [str(x) for x in vals]
        if isinstance(vals, str):
            return [v for v in re.split(r'[\s,]+', vals) if v]
    except Exception:
        pass
    vals = getattr(interp, 'variables', None)
    if isinstance(vals, dict) and name in vals:
        v = vals[name]
        if isinstance(v, list):  return [str(x) for x in v]
        if isinstance(v, str):   return [v]
    return []

def _exec_inner(line: str, interp, reg) -> str:
    res = reg.dispatch(line, interp)
    return _to_text(res)

def _scan_fields(s: str) -> List[Tuple[int,int,str]]:
    i=0; n=len(s); out=[]; esc=False; q=None
    while i<n:
        ch=s[i]
        if esc: esc=False; i+=1; continue
        if ch == '\\': esc=True; i+=1; continue
        if q:
            if ch == q: q=None
            i+=1; continue
        if ch in ('"', "'"): q=ch; i+=1; continue
        if ch in ('%','#') and i+1<n and s[i+1]=='(':
            op=ch; depth=1; j=i+2
            while j<n and depth>0:
                c=s[j]
                if c=='\\': j+=2; continue
                if c in ('"', "'"):
                    q2=c; j+=1
                    while j<n and s[j]!=q2:
                        if s[j]=='\\': j+=2; continue
                        j+=1
                    if j<n: j+=1
                    continue
                if c=='(':
                    depth+=1
                elif c==')':
                    depth-=1
                j+=1
            if depth==0:
                out.append((i, j, op)); i=j; continue
        i+=1
    return out[::-1]

_var_pat_strict = re.compile(r"^\s*\$(?:\((?P<n1>[A-Za-z_][A-Za-z0-9_]*)\)|(?P<n2>[A-Za-z_][A-Za-z0-9_]*))\s*$")
_var_pat_loose  = re.compile(r"\$(?:\((?P<n1>[A-Za-z_][A-Za-z0-9_]*)\)|(?P<n2>[A-Za-z_][A-Za-z0-9_]*))")

def _expand_vars_outside_fields(s: str, interp, fields: List[Tuple[int,int,str]]) -> str:
    if '$' not in s:
        return s
    # Build protected ranges from fields
    protected = [(a,b) for (a,b,_) in fields]
    def in_protected(idx: int) -> bool:
        for a,b in protected:
            if a <= idx < b:
                return True
        return False

    out = []
    i = 0
    while i < len(s):
        if s[i] != '$':
            out.append(s[i]); i+=1; continue
        m = _var_pat_loose.match(s, i)
        if not m:
            out.append('$'); i+=1; continue
        # Skip expansion if inside a field
        if in_protected(i):
            out.append(s[i:m.end()]); i=m.end(); continue
        name = m.group('n1') or m.group('n2')
        # Skip loop-variable expansion unless explicitly allowed
        if name == 'item' and not bool(getattr(interp, 'allow_loop_vars', False)):
            out.append(s[i:m.end()]); i = m.end(); continue
        vals = _get_var_vals(name, interp)
        repl = ','.join(vals) if vals else ''
        out.append(repl)
        i = m.end()
    return ''.join(out)

def expand_line(line: str, interp, reg) -> str:
    if not line:
        return line
    # First, identify fields and expand PLAIN variables *outside* them
    fields = _scan_fields(line)
    s = _expand_vars_outside_fields(line, interp, fields)

    # Re-scan fields (positions may have shifted but we only care about content)
    fields = _scan_fields(s)
    if not fields:
        return s

    for start, end, op in fields:
        inner = s[start+2:end-1]
        m = _var_pat_strict.match(inner)
        if m:
            name = m.group('n1') or m.group('n2')
            vals = _get_var_vals(name, interp)
            repl = '\n'.join(vals) if op=='%' else ','.join(vals)
        else:
            text = _exec_inner(inner.strip(), interp, reg)
            if op == '%':
                repl = text
            else:
                parts = [p for p in re.split(r'[\s,]+', text.strip()) if p]
                repl = ','.join(parts)
        s = s[:start] + repl + s[end:]
    return s

def get_executor(reg, interp):
    def _exec(line: str) -> str:
        allow = bool(getattr(interp, 'allow_loop_vars', False))
        return expand_line(line, interp, reg, allow_loop_vars=allow)
    return _exec
