# === VNLT REV ===
# file: vnlt.py
# rev:  2025-10-21 04:20  r2i  tag:cli
# note: Fix redirection parsing for '>>' by scanning from the right; keep attach/load_celllib_graph and all prior features.
# === /VNLT REV ===

import sys, os, subprocess
from pathlib import Path

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
            # preserve existing dict normalization semantics
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

    r = gt_indices[-1]  # rightmost '>'
    # Determine operator start for '>>' vs '>'
    op_start = r - 1 if r - 1 >= 0 and left[r-1] == '>' else r
    append = (op_start != r)

    j = r + 1  # path scanning starts after the rightmost '>'
    # Skip spaces
    while j < len(left) and left[j].isspace():
        j += 1
    if j >= len(left):
        return left, shell_tail, None, False

    # Parse filename token (quote-aware)
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

    # Remove operator (from op_start) and path from command; keep left side only
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

def _install_history():
    try:
        import readline, atexit
        hist = os.path.expanduser("~/.vnlt_history")
        try:
            readline.read_history_file(hist)
        except Exception:
            pass
        atexit.register(readline.write_history_file, hist)
    except Exception:
        pass

def run_repl(interp, reg):
    print(f"{APP_NAME} {APP_REV}")
    print("Type 'help' for a list of commands, or 'exit' to quit.")
    _install_history()
    while True:
        try:
            line = input("vnlt> ")
        except EOFError:
            print()
            break
        try:
            out = _dispatch_one(reg, interp, line)
            if out:
                print(out)
        except SystemExit:
            break
        except Exception as e:
            print(f"[ERROR] {e}")

def main():
    import argparse, glob, importlib.util
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--graph", default=None)
    ap.add_argument("--batch", default=None)
    args, _ = ap.parse_known_args()

    reg = CommandRegistry()

    class Interpreter:
        """Lightweight shared context that commands can fill.
        Provides attach() and load_celllib_graph() so legacy/new builders can load results.
        """
        def __init__(self, registry):
            self.registry = registry
            self.graph = None
            self.celllib = None
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

    this_dir = Path(__file__).resolve().parent
    cmds_dir = this_dir / "cmds"
    for path in sorted(glob.glob(str(cmds_dir / "cmd_*.py"))):
        modname = Path(path).stem
        try:
            spec = importlib.util.spec_from_file_location(modname, path)
            mod = importlib.util.module_from_spec(spec)
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
