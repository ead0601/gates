#!/usr/bin/env python3
# vnlt launcher

import argparse
import json
import os
import sys
import atexit
import subprocess
from pathlib import Path

# Ensure this file's directory is importable so bare "cmd_*.py" imports work
_SCRIPT_DIR = str(Path(__file__).parent.resolve())
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from registry import CommandRegistry, set_global_registry  # noqa: E402
from core import Interpreter  # noqa: E402

APP_NAME = "vnlt"
VERSION = "0.6.5"

# ----- line editing / history (↑/↓, ←/→, Tab) -------------------------------
try:
    import readline  # type: ignore
    _HIST = os.path.expanduser("~/.vnlt_history")
    try:
        readline.read_history_file(_HIST)
    except FileNotFoundError:
        pass
    readline.set_history_length(2000)
    atexit.register(readline.write_history_file, _HIST)
    # base keybinds
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
except Exception:
    readline = None  # on Windows or if module missing
# ---------------------------------------------------------------------------

def _print_raw(text: str):
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()

def _print_banner():
    _print_raw(f"{APP_NAME} v{VERSION} — Verilog Netlist CLI")
    _print_raw("Type 'help' for a list of commands, or 'help <cmd>' for details.")

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

def _split_pipeline_and_redirect(line: str):
    """
    Split a line into (vnlt_cmd, shell_pipeline_or_None, out_path_or_None, append_flag).
    Supports a single pipeline chunk (which itself can have multiple pipes and args).
    If the pipeline starts with '$(' and ends with ')', those are stripped.
    Redirection ( > or >> ) is parsed from the end of the whole line.
    """
    s = line.strip()

    # Parse redirection from the end first
    redir_idxs = _scan_tokens(s, '>')
    out_path = None
    append = False
    if redir_idxs:
        i = redir_idxs[-1]
        head = s[:i].rstrip()
        tail = s[i + 1:].lstrip()
        if tail.startswith('>'):
            append = True
            tail = tail[1:].lstrip()
        if tail:
            # filename may be quoted or bare
            if tail[0] in ("'", '"'):
                q = tail[0]
                j = tail.find(q, 1)
                out_path = tail[1:j] if j != -1 else tail[1:]
            else:
                out_path = tail.split()[0]
            s = head  # strip the redirection part from the working string

    # Split pipeline on the first unquoted '|'
    pipe_idxs = _scan_tokens(s, '|')
    shell_pipe = None
    if pipe_idxs:
        i = pipe_idxs[0]
        vnlt_cmd = s[:i].strip()
        shell_pipe = s[i + 1:].strip()
        # optional $( ... ) wrapper
        if shell_pipe.startswith('$(') and shell_pipe.endswith(')'):
            shell_pipe = shell_pipe[2:-1].strip()
    else:
        vnlt_cmd = s

    return vnlt_cmd, shell_pipe, out_path, append

def _split_redirect(line: str):
    # Backward-compat wrapper for any callers still using this directly
    vnlt_cmd, _, out_path, append = _split_pipeline_and_redirect(line)
    return vnlt_cmd, out_path, append

def load_builtin_commands(reg: CommandRegistry):
    """
    Attempt to import a curated set of cmd_* modules and call register(reg) if present.
    Modules marked required=True will log as [ERROR] on failure; others as [WARN].
    """
    modules = [
        ("cmd_help", True),
        ("cmd_exit", True),
        ("cmd_list", True),
        ("cmd_find", True),
        ("cmd_cat", True),
        ("cmd_ls", True),
        ("cmd_show", False),
        ("cmd_fanin", False),
        ("cmd_fanout", False),
        ("cmd_paths", False),  # alias 'path'
        ("cmd_read_verilog", True),
    ]
    for mod, required in modules:
        try:
            m = __import__(mod)
        except Exception as e:
            tag = "ERROR" if required else "WARN"
            _print_raw(f"[{tag}] could not load {mod}: {e}")
            continue
        try:
            if hasattr(m, "register"):
                m.register(reg)
            else:
                _print_raw(f"[WARN] {mod} has no register(reg)")
        except Exception as e:
            tag = "ERROR" if required else "WARN"
            _print_raw(f"[{tag}] {mod}.register failed: {e}")

def _install_basic_completer(reg: CommandRegistry):
    if readline is None:
        return
    try:
        cmds = sorted(reg.list_commands())
        def _vnlt_completer(text, state):
            matches = [c for c in cmds if c.startswith(text)]
            return matches[state] if state < len(matches) else None
        readline.set_completer(_vnlt_completer)
        readline.parse_and_bind("tab: complete")
    except Exception:
        pass

def _res_to_text(res):
    if isinstance(res, dict) and "__raw" in res:
        return res["__raw"]
    if isinstance(res, str):
        return res
    try:
        return json.dumps(res, sort_keys=False)
    except Exception:
        return str(res)

def run_repl(interp: Interpreter, reg: CommandRegistry):
    _print_banner()
    _install_basic_completer(reg)
    prompt = "vnlt> "
    while True:
        try:
            line = input(prompt)
        except EOFError:
            _print_raw("")  # newline on Ctrl-D
            break
        except KeyboardInterrupt:
            _print_raw("")  # newline on Ctrl-C
            continue

        if not line.strip():
            continue

        cmdline, shell_pipe, out_path, append = _split_pipeline_and_redirect(line)
        res = reg.execute(cmdline, interp)
        if not res:
            continue

        # Exit handling
        if isinstance(res, dict) and res.get("cmd") == "quit":
            break

        # Apply shell pipeline if requested
        if shell_pipe:
            _txt = _res_to_text(res)
            try:
                proc = subprocess.run(shell_pipe, input=_txt.encode("utf-8"), shell=True, capture_output=True)
                res = {"__raw": proc.stdout.decode("utf-8", errors="replace")}
            except Exception as e:
                res = {"__raw": f"[ERROR] pipeline failed: {e}\n"}

        # Output handling (stdout or file)
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
            continue

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
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            cmdline, shell_pipe, out_path, append = _split_pipeline_and_redirect(line)
            res = reg.execute(cmdline, interp)
            if not res:
                continue

            if isinstance(res, dict) and res.get("cmd") == "quit":
                return

            # Apply pipeline in batch too
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
                continue

            if isinstance(res, dict) and "__raw" in res:
                _print_raw(res["__raw"])
            else:
                try:
                    print(json.dumps(res, sort_keys=False))
                except Exception:
                    print(res)

def main():
    ap = argparse.ArgumentParser(prog="verilog_parse.py")
    ap.add_argument(
        "--graph",
        help="Path to netgraph.json (optional; can load later via 'read verilog')",
    )
    ap.add_argument(
        "-m",
        "--manifest",
        help="Path to a Verilog manifest (.lst/.txt) to load at startup",
    )
    ap.add_argument(
        "-y",
        "--batch",
        help="Run commands from a file (blank lines and # comments ignored)",
    )
    args = ap.parse_args()

    reg = CommandRegistry()
    set_global_registry(reg)
    load_builtin_commands(reg)

    interp = Interpreter()

    # Optional preloaded graph
    if args.graph:
        try:
            interp.load_graph(Path(args.graph))
        except Exception as e:
            _print_raw(f"[WARN] could not load graph '{args.graph}': {e}")

    # Auto-load manifest if provided
    if args.manifest:
        res = reg.execute(f"read verilog {args.manifest}", interp)
        if res:
            if isinstance(res, dict) and res.get("cmd") == "quit":
                return
            if isinstance(res, dict) and "__raw" in res:
                _print_raw(res["__raw"])
            else:
                try:
                    print(json.dumps(res, sort_keys=False))
                except Exception:
                    print(res)

    # Batch or interactive
    if args.batch:
        run_batch(interp, reg, Path(args.batch))
    else:
        run_repl(interp, reg)

if __name__ == "__main__":
    main()
