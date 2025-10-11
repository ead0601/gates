# === VNLT REV ===
# file: python/verilog_parse.py
# rev:  2025-10-11  r5  by:ediaz  tag:core
# note: Pre-dispatch $(...) expansion (no monkey-patch); in-memory capture; preserves pipes/redirects
# === /VNLT REV ===

import argparse
import json
import os
import sys
import atexit
import subprocess
import importlib.util
from pathlib import Path
import re

# Ensure this file's directory is importable so "import cmd_*.py" works
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Your framework pieces
from registry import CommandRegistry, set_global_registry   # noqa: E402
from core import Interpreter                                # noqa: E402

APP_NAME = "vnlt"
VERSION  = "0.6.6"

# ---------- line editing / history ----------
try:
    import readline  # type: ignore
    _HIST = os.path.expanduser("~/.vnlt_history")
    try:
        readline.read_history_file(_HIST)
    except FileNotFoundError:
        pass
    readline.set_history_length(2000)
    atexit.register(readline.write_history_file, _HIST)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
except Exception:
    readline = None

def _print_raw(text: str):
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()

def _res_to_text(res):
    if isinstance(res, dict) and "__raw" in res:
        return res["__raw"]
    if isinstance(res, str):
        return res
    try:
        return json.dumps(res, sort_keys=False)
    except Exception:
        return str(res)

def _scan_tokens(line: str, target_chars: str):
    """Return indices of unquoted target chars in the line (simple shell-ish scan)."""
    idxs = []
    q = None
    esc = False
    for i, ch in enumerate(line):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if q:
            if ch == q:
                q = None
            continue
        if ch in ('"', "'"):
            q = ch
            continue
        if ch in target_chars:
            idxs.append(i)
    return idxs

def _split_pipeline_and_redirect(s: str):
    """
    Returns (vnlt_cmd, shell_pipeline_or_None, out_path_or_None, append_flag).
    Supports a single pipeline chunk; if it starts with '$(') and ends with ')', those are stripped.
    Parses trailing redirection (> or >>) to filename (quoted or bare).
    """
    s = s.strip()

    # Parse redirection from the end first
    redir_idxs = _scan_tokens(s, '>')
    out_path = None
    append = False
    if redir_idxs:
        i = redir_idxs[-1]
        head = s[:i].rstrip()
        tail = s[i + 1 :].lstrip()
        if tail.startswith('>'):
            append = True
            tail = tail[1:].lstrip()
        if tail:
            if tail[0] in ("'", '"'):
                q = tail[0]
                j = tail.find(q, 1)
                out_path = tail[1:j] if j != -1 else tail[1:]
            else:
                out_path = tail.split()[0]
            s = head  # remaining string without redirection

    # Split pipeline on the first unquoted '|'
    pipe_idxs = _scan_tokens(s, '|')
    shell_pipe = None
    if pipe_idxs:
        i = pipe_idxs[0]
        vnlt_cmd = s[:i].strip()
        shell_pipe = s[i + 1 :].strip()
        if shell_pipe.startswith('$(') and shell_pipe.endswith(')'):
            shell_pipe = shell_pipe[2:-1].strip()
    else:
        vnlt_cmd = s

    return vnlt_cmd, shell_pipe, out_path, append

# ----------------------------
# Built-in capture and $(...) expansion
# ----------------------------
def execute_one_line_and_capture_text(line: str, interp: Interpreter, reg: CommandRegistry) -> str:
    """
    Execute *one* vnlt line through the exact same per-line path as interactive execution,
    apply any shell pipeline on that line, but IGNORE final redirection (> >>).
    Return the final textual stdout the REPL would print.
    """
    vnlt_cmd, shell_pipe, out_path, _append = _split_pipeline_and_redirect(line)

    # Run vnlt part
    res = reg.execute(vnlt_cmd, interp)
    if isinstance(res, dict) and res.get("cmd") == "quit":
        # Captures nothing for quit
        return ""

    # Apply shell pipe if present
    if shell_pipe:
        _txt = _res_to_text(res) if res is not None else ""
        try:
            proc = subprocess.run(shell_pipe, input=_txt.encode("utf-8"), shell=True, capture_output=True)
            text = proc.stdout.decode("utf-8", errors="replace")
        except Exception as e:
            text = f"[ERROR] pipeline failed: {e}\n"
    else:
        text = _res_to_text(res) if res is not None else ""

    # Ignore redirection for capture: just return the text
    return text

def _expand_dollar_parens_pre(line: str, interp: Interpreter, reg: CommandRegistry) -> str:
    """Expand all non-nested $(...) on the RAW line before parsing pipes/redirects."""
    out = []
    i = 0
    s = line
    while i < len(s):
        j = s.find("$(", i)
        if j == -1:
            out.append(s[i:])
            break
        # append prefix
        out.append(s[i:j])
        # find matching ')', non-nested but quote-aware
        k = j + 2
        q = None
        esc = False
        while k < len(s):
            ch = s[k]
            if esc:
                esc = False; k += 1; continue
            if ch == "\\":
                esc = True; k += 1; continue
            if q:
                if ch == q:
                    q = None
                k += 1; continue
            if ch in ('"', "'"):
                q = ch; k += 1; continue
            if ch == ')':
                break
            k += 1
        if k >= len(s) or s[k] != ')':
            # unmatched, leave literal remainder
            out.append(s[j:])
            break
        inner = s[j+2:k].strip()
        captured = execute_one_line_and_capture_text(inner, interp, reg)
        # newline split -> tokens; drop empties; strip CR/LF
        items = []
        for raw in captured.splitlines():
            t = raw.replace('\r','').strip()
            if t:
                items.append(t)
        out.append(" ".join(items))
        i = k + 1
    return "".join(out)

# ----------------------------
# Command execution helpers
# ----------------------------
def _exec_core(cmdline: str, interp: Interpreter, reg: CommandRegistry):
    """Execute a vnlt command line with pipeline/redirection handling; return dict/str."""
    # NEW: expand $(...) on the raw line first
    expanded = _expand_dollar_parens_pre(cmdline, interp, reg)

    vnlt_cmd, shell_pipe, out_path, append = _split_pipeline_and_redirect(expanded)
    res = reg.execute(vnlt_cmd, interp)
    if not res:
        return None

    if isinstance(res, dict) and res.get("cmd") == "quit":
        return res

    if shell_pipe:
        _txt = _res_to_text(res)
        try:
            proc = subprocess.run(shell_pipe, input=_txt.encode("utf-8"), shell=True, capture_output=True)
            res = {"__raw": proc.stdout.decode("utf-8", errors="replace")}
        except Exception as e:
            res = {"__raw": f"[ERROR] pipeline failed: {e}\n"}

    if out_path:
        text = _res_to_text(res)
        mode = "a" if append else "w"
        try:
            with open(out_path, mode, encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
        except Exception as e:
            _print_raw(f"[ERROR] could not write to '{out_path}': {e}")
        return None

    return res

# ----------------------------
# Auto-discover and register cmd_*.py in this directory
# ----------------------------
def _auto_discover_and_register(reg: CommandRegistry):
    for p in sorted(_SCRIPT_DIR.glob("cmd_*.py")):
        if p.name == Path(__file__).name:
            continue
        try:
            spec = importlib.util.spec_from_file_location(p.stem, p)
            if not spec or not spec.loader:
                _print_raw(f"[WARN] could not prepare import for {p.name}")
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[p.stem] = mod
            spec.loader.exec_module(mod)
            reg_fn = getattr(mod, "register", None)
            if callable(reg_fn):
                reg_fn(reg)
        except Exception as e:
            _print_raw(f"[WARN] {p.name}.register failed: {e}")

# ----------------------------
# REPL / Batch
# ----------------------------
def _print_banner():
    _print_raw(f"{APP_NAME} v{VERSION} — Verilog Netlist CLI")
    _print_raw("Type 'help' for a list of commands, or 'help <cmd>' for details.")

def run_repl(interp: Interpreter, reg: CommandRegistry):
    _print_banner()
    prompt = "vnlt> "
    while True:
        try:
            line = input(prompt)
        except EOFError:
            _print_raw("")
            break
        except KeyboardInterrupt:
            _print_raw("")
            continue
        s = line.strip()
        if not s:
            continue
        res = _exec_core(s, interp, reg)
        if res is None:
            continue
        if isinstance(res, dict) and res.get("cmd") == "quit":
            break
        if isinstance(res, dict) and "__raw" in res:
            _print_raw(res["__raw"])
        else:
            try:
                print(json.dumps(res, sort_keys=False))
            except Exception:
                print(res)

def run_batch(interp: Interpreter, reg: CommandRegistry, batch_path: Path):
    if not batch_path.exists():
        _print_raw(f"[ERROR] batch file not found: {batch_path}")
        return
    with batch_path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            res = _exec_core(s, interp, reg)
            if res is None:
                continue
            if isinstance(res, dict) and res.get("cmd") == "quit":
                return
            if isinstance(res, dict) and "__raw" in res:
                _print_raw(res["__raw"])
            else:
                try:
                    print(json.dumps(res, sort_keys=False))
                except Exception:
                    print(res)

# ----------------------------
# Main
# ----------------------------
def main():
    ap = argparse.ArgumentParser(prog="verilog_parse.py")
    ap.add_argument("--graph", help="Path to netgraph.json (optional; can load later via 'read verilog')")
    ap.add_argument("-m", "--manifest", help="Path to a Verilog manifest (.lst/.txt) to load at startup")
    ap.add_argument("-y", "--batch", help="Run commands from a file (blank lines and # comments ignored)")
    args = ap.parse_args()

    reg = CommandRegistry()
    set_global_registry(reg)

    # Auto-discover all cmd_*.py alongside this file (default python dir)
    _auto_discover_and_register(reg)

    interp = Interpreter()

    if args.graph:
        try:
            interp.load_graph(Path(args.graph))
        except Exception as e:
            _print_raw(f"[WARN] could not load graph '{args.graph}': {e}")

    if args.manifest:
        res = _exec_core(f"read verilog {args.manifest}", interp, reg)
        if isinstance(res, dict) and "__raw" in res:
            _print_raw(res["__raw"])

    if args.batch:
        run_batch(interp, reg, Path(args.batch))
    else:
        run_repl(interp, reg)

if __name__ == "__main__":
    main()
