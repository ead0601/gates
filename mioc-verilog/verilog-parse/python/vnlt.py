# === VNLT REV ===
# file: vnlt.py
# note: r2i+forpipe — special-case one-line 'for ... ; end' so the REPL does NOT
#       split on top-level '|'/'>' before handing it to cmd_for. This allows
#       pipes/redirects inside the loop body.
# note: r2i+multiline — add '\' line-continuation in REPL.
# note: r2i+histline — store exactly ONE logical line per history entry (so Up arrow recalls the full, concatenated command).
# === /VNLT REV ===

import sys, os, subprocess, glob
from pathlib import Path
import importlib.util as importlib_util
import argparse

from registry import CommandRegistry
from expander_runtime import expand_line

APP_NAME = "vnlt-reboot"
APP_REV  = "r2i"

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
            vals = res.get('fields') or []
            try:
                return ','.join(str(x) for x in vals)
            except Exception:
                return '\n'.join(str(x) for x in vals)
    return str(res)

# Special-case detector for one-line 'for ... ; end'
def _is_oneline_for(s: str) -> bool:
    if not s: return False
    st = s.strip()
    if not st.startswith("for "): return False
    return st.endswith("end") or bool(__import__("re").search(r";\s*end\s*$", st))

def _scan_unquoted(s: str, target: str):
    esc=False; q=None; i=0; n=len(s)
    while i<n:
        ch=s[i]
        if esc: esc=False; i+=1; continue
        if ch == '\\': esc=True; i+=1; continue
        if q:
            if ch == q: q=None
            i+=1; continue
        if ch in ('"', "'"): q=ch; i+=1; continue
        if ch == target:
            yield i
        i+=1

def _split_pipeline_and_redirect(s: str):
    left = s.strip()
    shell_tail = None
    # Split vnlt|shell (first unquoted |)
    for i in _scan_unquoted(left, '|'):
        shell_tail = left[i+1:].strip()
        left = left[:i].strip()
        break

    # Find the RIGHTMOST unquoted '>'
    gt_indices = list(_scan_unquoted(left, '>'))
    if not gt_indices:
        return left, shell_tail, None, False

    r = gt_indices[-1]
    op_start = r - 1 if r - 1 >= 0 and left[r-1] == '>' else r
    append = (op_start != r)

    j = r + 1
    while j < len(left) and left[j].isspace():
        j += 1
    if j >= len(left):
        return left, shell_tail, None, False

    if left[j] in ('"', "'"):
        q = left[j]; j += 1
        k = j
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

def _dispatch_one(reg: CommandRegistry, interp, raw_line: str):
    if not raw_line or not raw_line.strip():
        return ''
    expanded = expand_line(raw_line, interp, reg)

    # Skip top-level splitting for a one-line 'for ... ; end'
    if _is_oneline_for(expanded):
        left = expanded
        shell_tail = None
        out_path = None
        append = False
    else:
        left, shell_tail, out_path, append = _split_pipeline_and_redirect(expanded)

    res = reg.dispatch(left, interp)
    text = _res_to_text(res)

    if shell_tail:
        p = subprocess.Popen(['/bin/sh','-c', shell_tail], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(text)
        text = out

    if out_path:
        _write_redirect(out_path, text, append)
        return ''

    return text

# --- History management (one logical line per entry) ---
_readline = None
def _install_history():
    global _readline
    try:
        import readline as _readline  # keep reference
        import atexit
        # Turn off auto history so partial continuation lines are NOT recorded
        try:
            _readline.set_auto_history(False)
        except Exception:
            pass
        hist = os.path.expanduser("~/.vnlt_history")
        try:
            _readline.read_history_file(hist)
        except Exception:
            pass
        atexit.register(lambda: _safe_write_history(hist))
    except Exception:
        _readline = None

def _safe_write_history(path):
    try:
        if _readline:
            _readline.write_history_file(path)
    except Exception:
        pass

# --- BEGIN: multiline input helper ---
def _read_continued_line(primary_prompt="vnlt> ", cont_prompt="... "):
    """
    Read a logical command line with '\' continuation.
    If the user ends a line with a single backslash, do not dispatch yet;
    keep reading subsequent lines until we get one that doesn't end in '\'.
    The final returned string is the concatenation of the pieces (with the
    continuation backslashes removed).

    Notes:
      - To input a literal trailing backslash, escape it as '\\\\' at end.
      - Only the last character matters; trailing spaces AFTER '\\' will cancel
        continuation (because the last char is not backslash).
    """
    parts = []
    first = True
    while True:
        try:
            raw = input(primary_prompt if first else cont_prompt)
        except EOFError:
            # Ctrl-D / EOF
            return None
        if raw is None:
            return None

        # Continue only if the LAST character is a backslash
        if len(raw) > 0 and raw[-1] == '\\':
            parts.append(raw[:-1])  # drop the trailing backslash
            first = False
            continue

        parts.append(raw)
        return "".join(parts)
# --- END: multiline input helper ---

def run_repl(interp, reg):
    print(f"{APP_NAME} {APP_REV}")
    print("Type 'help' for a list of commands, or 'exit' to quit.")
    _install_history()
    while True:
        try:
            # Read one logical line (may span multiple physical lines)
            line = _read_continued_line("vnlt> ", "... ")
            if line is None:
                print()
                break
        except EOFError:
            print()
            break

        # Store exactly one history entry (the concatenated command)
        try:
            if _readline and line.strip():
                _readline.add_history(line)
        except Exception:
            pass

        try:
            out = _dispatch_one(reg, interp, line)
            if out:
                print(out)
        except SystemExit:
            break
        except Exception as e:
            print(f"[ERROR] {e}")

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('-v','--verbose', action='store_true')
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--graph", default=None)
    ap.add_argument("--batch", default=None)
    args, _ = ap.parse_known_args()

    reg = CommandRegistry()

    class Interpreter:
        def __init__(self, registry):
            self.registry = registry
            self.graph = None
            self.celllib = None
            self.debug = False
        def attach(self, graph=None, celllib=None, **kwargs):
            if celllib is not None:
                self.celllib = celllib
            if graph is not None:
                self.graph = graph
            return True
        def load_celllib_graph(self, celllib, graph):
            self.celllib = celllib
            self.graph = graph
            return True

    interp = Interpreter(reg)
    try:
        interp.debug = bool(args.verbose) or bool(int(os.getenv('VNLT_DEBUG','0') or '0'))
    except Exception:
        interp.debug = bool(args.verbose)

    this_dir = Path(__file__).resolve().parent
    cmds_dir = this_dir / "cmds"
    for path in sorted(glob.glob(str(cmds_dir / "cmd_*.py"))):
        modname = Path(path).stem
        try:
            spec = importlib_util.spec_from_file_location(modname, path)
            mod = importlib_util.module_from_spec(spec)
            sys.modules[modname] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                mod.register(reg)
        except Exception as e:
            print(f"[WARN] failed to import {modname}: {e}")

    if args.manifest:
        try:
            _ = _dispatch_one(reg, interp, f"read_verilog {args.manifest}")
        except Exception as e:
            print(f"[ERROR] read_verilog failed: {e}")

    if args.batch:
        p = Path(args.batch).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if not p.exists():
            print(f"[ERROR] batch file not found: {p}")
        else:
            for raw in p.read_text(errors='ignore').splitlines():
                cut = raw.split('#', 1)[0].strip()
                if not cut:
                    continue
                try:
                    out = _dispatch_one(reg, interp, cut)
                    if out:
                        print(out)
                except SystemExit:
                    break
                except Exception as e:
                    print(f"[ERROR] {e}")
            return

    run_repl(interp, reg)

if __name__ == "__main__":
    main()
