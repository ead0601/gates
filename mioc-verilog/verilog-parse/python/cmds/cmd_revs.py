# === VNLT REV ===
# file: cmds/cmd_revs.py
# rev:  2025-10-19 01:17  r2c+revs6  by:Drater  tag:cmd
# note: show 'path  timestamp  r#' (still aligned); ignores by:/tag:
# === /VNLT REV ===

from registry import CommandRegistry
import os, re

START = '# === VNLT REV ==='
END   = '# === /VNLT REV ==='
RX    = re.compile(r"\brev:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+([^\s#]+)", re.IGNORECASE)

def _parse_rev_ts_r(lines, i):
    ts = ''
    rtag = ''
    i += 1
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith(END):
            break
        if s.startswith('#'):
            body = s.lstrip('#').strip()
            m = RX.search(body)
            if m:
                ts, rtag = m.group(1), m.group(2)
        i += 1
    return ts, rtag, i

def _scan_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
    except Exception:
        return []
    res=[]; i=0
    while i < len(lines):
        if lines[i].strip().startswith(START):
            ts, rtag, i = _parse_rev_ts_r(lines, i)
            if ts:
                res.append((path, ts, rtag))
        else:
            i += 1
    return res

def _walk(root):
    out=[]
    for dp, dn, fn in os.walk(root):
        if '__pycache__' in dp:
            continue
        for f in fn:
            out.extend(_scan_file(os.path.join(dp,f)))
    return out

def _handler(rest, interp):
    root = (rest or '').strip() or os.getcwd()
    items = sorted(_walk(root), key=lambda t: t[0])
    if not items:
        return ''
    w = max(len(p) for p,_,_ in items)
    return '\n'.join([p.ljust(w) + '  ' + ts + (('  ' + (rtag or '')) if rtag else '') for p,ts,rtag in items])

def register(reg: CommandRegistry):
    reg.register('revs', _handler, 'revs [path] — list file, timestamp, r# (aligned)')
