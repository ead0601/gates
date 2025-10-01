#!/usr/bin/env python3
# vnlt launcher with variables & foreach
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

# ---------- tiny state for Option B ----------
_VARS = {}  # name -> List[str]


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


def _split_pipeline_and_redirect(s: str):
    """
    Returns (vnlt_cmd, shell_pipeline_or_None, out_path_or_None, append_flag).
    Supports a single pipeline chunk; if it starts with '$(' and ends with ')', those are stripped.
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


def _res_to_text(res):
    if isinstance(res, dict) and "__raw" in res:
        return res["__raw"]
    if isinstance(res, str):
        return res
    try:
        return json.dumps(res, sort_keys=False)
    except Exception:
        return str(res)


def load_builtin_commands(reg: CommandRegistry):
    mods = [
        ("cmd_help", True),
        ("cmd_exit", True),
        ("cmd_list", True),
        ("cmd_find", True),
        ("cmd_cat", True),
        ("cmd_ls", True),
        ("cmd_show", False),
        ("cmd_fanin", False),
        ("cmd_fanout", False),
        ("cmd_paths", False),
        ("cmd_read_verilog", True),
    ]
    for mod, required in mods:
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
        cmds = sorted(reg.list_commands()) + ["set", "vars", "unset", "foreach"]
        def _vnlt_completer(text, state):
            matches = [c for c in cmds if c.startswith(text)]
            return matches[state] if state < len(matches) else None
        readline.set_completer(_vnlt_completer)
        readline.parse_and_bind("tab: complete")
    except Exception:
        pass


def _exec_core(cmdline: str, interp: Interpreter, reg: CommandRegistry):
    """Execute a vnlt command line with pipeline/redirection handling; return dict/str."""
    vnlt_cmd, shell_pipe, out_path, append = _split_pipeline_and_redirect(cmdline)
    res = reg.execute(vnlt_cmd, interp)
    if not res:
        return None

    # handle exit
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
        return None  # nothing to print to stdout

    return res


def _handle_meta(line: str, interp: Interpreter, reg: CommandRegistry):
    """Return True if handled (printed), False if not a meta-command, or 'QUIT' to exit."""
    s = line.strip()
    if not s:
        return True

    # ---- set NAME = $( <vnlt-cmd> [| shell ...] )  OR  set NAME = literal ... ----
    if s.startswith("set "):
        try:
            # split: set NAME = RHS
            _, rest = s.split(" ", 1)
            name, rhs = rest.split("=", 1)
            name = name.strip()
            rhs = rhs.strip()
            items = []
            if rhs.startswith("$(") and rhs.endswith(")"):
                inner = rhs[2:-1].strip()
                # run inner via core executor but ignore its redirection
                vnlt_cmd, shell_pipe, _, _ = _split_pipeline_and_redirect(inner)
                res = reg.execute(vnlt_cmd, interp)
                if res:
                    if shell_pipe:
                        _txt = _res_to_text(res)
                        try:
                            proc = subprocess.run(shell_pipe, input=_txt.encode("utf-8"), shell=True, capture_output=True)
                            res = {"__raw": proc.stdout.decode("utf-8", errors="replace")}
                        except Exception as e:
                            res = {"__raw": f"[ERROR] pipeline failed: {e}\n"}
                    text = _res_to_text(res)
                    for line in text.splitlines():
                        t = line.strip()
                        if t:
                            items.append(t)
            else:
                # literal list: split on spaces, keep quotes content
                # very light tokenizer: split by spaces unless inside quotes
                buf = ""
                q = None
                def flush():
                    nonlocal buf
                    if buf != "":
                        items.append(buf)
                        buf = ""
                for ch in rhs:
                    if q:
                        if ch == q:
                            q = None
                        else:
                            buf += ch
                        continue
                    if ch in ("'", '"'):
                        q = ch
                        continue
                    if ch.isspace():
                        flush()
                        continue
                    buf += ch
                flush()

            _VARS[name] = items
            _print_raw(f"[set] {name} = {len(items)} item(s)")
        except Exception as e:
            _print_raw(f"[ERROR] set: {e}")
        return True

    # ---- vars / vars NAME ----
    if s == "vars":
        if not _VARS:
            _print_raw("(no vars)")
        else:
            for k, v in _VARS.items():
                _print_raw(f"{k} : {len(v)}")
        return True
    if s.startswith("vars "):
        name = s.split(" ", 1)[1].strip()
        vals = _VARS.get(name)
        if vals is None:
            _print_raw(f"[vars] {name} : <unset>")
        else:
            for it in vals:
                _print_raw(it)
        return True

    # ---- unset NAME ----
    if s.startswith("unset "):
        name = s.split(" ", 1)[1].strip()
        if name in _VARS:
            del _VARS[name]
            _print_raw(f"[unset] {name}")
        else:
            _print_raw(f"[unset] {name} : <unset>")
        return True

    # ---- foreach item in $NAME [--echo] [--limit N] do BODY end ----
    if s.startswith("foreach "):
        try:
            # crude parse
            # foreach <iter> in $<NAME> [--echo] [--limit N] do <BODY> end
            rest = s[len("foreach "):].strip()
            # split on ' do ' (first occurrence), and ensure ending ' end'
            do_idx = rest.find(" do ")
            if do_idx == -1 or not rest.endswith(" end"):
                raise ValueError("usage: foreach <iter> in $<NAME> [--echo] [--limit N] do <BODY> end")
            head = rest[:do_idx].strip()
            body = rest[do_idx+4:-4].strip()

            # parse head: "<iter> in $<NAME> [--echo] [--limit N]"
            parts = head.split()
            if len(parts) < 3 or parts[1] != "in" or not parts[2].startswith("$"):
                raise ValueError("bad head, want: <iter> in $<NAME> [--echo] [--limit N]")
            iter_name = parts[0]
            list_name = parts[2][1:]
            echo = False
            limit = None
            i = 3
            while i < len(parts):
                if parts[i] == "--echo":
                    echo = True
                    i += 1
                elif parts[i] == "--limit":
                    if i+1 >= len(parts):
                        raise ValueError("--limit needs a number")
                    try:
                        limit = int(parts[i+1])
                    except Exception:
                        raise ValueError("--limit needs an integer")
                    i += 2
                else:
                    raise ValueError(f"unknown option: {parts[i]}")

            items = _VARS.get(list_name) or []
            total = len(items) if limit is None else min(len(items), limit)
            for idx, val in enumerate(items[:total], 1):
                # expand $iter_name / ${iter_name}
                expanded = body.replace(f"${{{iter_name}}}", val).replace(f"${iter_name}", val)
                if echo:
                    _print_raw(f"[{idx}/{total}] {expanded}")
                res = _exec_core(expanded, interp, reg)
                if res is None:
                    continue
                if isinstance(res, dict) and res.get("cmd") == "quit":
                    return "QUIT"
                if isinstance(res, dict) and "__raw" in res:
                    _print_raw(res["__raw"])
                else:
                    try:
                        print(json.dumps(res, sort_keys=False))
                    except Exception:
                        print(res)
        except Exception as e:
            _print_raw(f"[ERROR] foreach: {e}")
        return True

    return False


def run_repl(interp: Interpreter, reg: CommandRegistry):
    _print_banner()
    _install_basic_completer(reg)
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

        if not line.strip():
            continue

        # meta commands first
        handled = _handle_meta(line, interp, reg)
        if handled == "QUIT":
            break
        if handled:
            continue

        res = _exec_core(line, interp, reg)
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
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            handled = _handle_meta(line, interp, reg)
            if handled == "QUIT":
                return
            if handled:
                continue

            res = _exec_core(line, interp, reg)
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


def main():
    ap = argparse.ArgumentParser(prog="verilog_parse.py")
    ap.add_argument("--graph", help="Path to netgraph.json (optional; can load later via 'read verilog')")
    ap.add_argument("-m", "--manifest", help="Path to a Verilog manifest (.lst/.txt) to load at startup")
    ap.add_argument("-y", "--batch", help="Run commands from a file (blank lines and # comments ignored)")
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
        res = _exec_core(f"read verilog {args.manifest}", interp, reg)
        if isinstance(res, dict) and "__raw" in res:
            _print_raw(res["__raw"])

    # Batch or interactive
    if args.batch:
        run_batch(interp, reg, Path(args.batch))
    else:
        run_repl(interp, reg)


if __name__ == "__main__":
    main()
