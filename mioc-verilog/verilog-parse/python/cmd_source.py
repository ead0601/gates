# REV:r9
# cmd_source.py — source [--raw] [--no-echo] <path>
# Executes each line exactly like typed. Captures EVERYTHING (direct prints to stdout/stderr
# and handler return values), composes it, and RETURNS the final text so shell redirection
# (>, >>) and pipes (|) work with zero leakage to the terminal.
#
# Default composed text policy per line:
#   - Echo: 'vnlt> <line>\n' (unless --no-echo)
#   - Captured stdout/stderr from the line, verbatim
#   - If handler returned a non-empty value:
#       * --raw  : append the raw text form (stringified if needed), ensure trailing \n
#       * default: append repr(value) + '\n' (mimic REPL display of return)

import os
import io
import sys

try:
    from verilog_parse import _exec_core as _repl_exec_one_line
except Exception:
    _repl_exec_one_line = None

def _parse_args(args):
    echo = True
    want_raw = False
    path = None
    for a in args:
        if a == "--no-echo":
            echo = False
        elif a == "--raw":
            want_raw = True
        elif a.startswith("--"):
            return None, None, f"source: unknown option: {a}"
        else:
            if path is not None:
                return None, None, "source: usage: source [--raw] [--no-echo] <path>"
            path = a
    if path is None:
        return None, None, "source: usage: source [--raw] [--no-echo] <path>"
    return (echo, want_raw, path)

def _normalize_raw(res):
    # Convert various handler return shapes into a raw string payload.
    if res is None:
        return ""
    if isinstance(res, str):
        return res
    if isinstance(res, (tuple, list)) and res:
        head = res[0]
        return head if isinstance(head, str) else ""
    if isinstance(res, dict) and "__raw" in res and isinstance(res["__raw"], str):
        return res["__raw"]
    # Fallback stringification
    return str(res)

def register(reg):
    def _source(args, interp=None):
        parsed = _parse_args(args)
        if isinstance(parsed, tuple) and len(parsed) == 3 and isinstance(parsed[2], str):
            echo, want_raw, path = parsed
        else:
            return parsed if isinstance(parsed, str) else "source: usage: source [--raw] [--no-echo] <path>"

        if _repl_exec_one_line is None:
            return "source: internal error: REPL single-line executor not available"
        if not os.path.isfile(path):
            return f"source: no such file: {path}"

        out_parts = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, rawline in enumerate(f, 1):
                line = rawline.rstrip("\n")
                if line.strip() == "":
                    continue
                # Compose per-line output
                if echo:
                    out_parts.append(f"vnlt> {line}\n")
                # Capture direct prints
                cap_out = io.StringIO()
                cap_err = io.StringIO()
                old_out, old_err = sys.stdout, sys.stderr
                try:
                    sys.stdout, sys.stderr = cap_out, cap_err
                    res = _repl_exec_one_line(line, interp, reg)
                except Exception as e:
                    # Restore and record error
                    sys.stdout, sys.stderr = old_out, old_err
                    out_parts.append(f"source:{idx}: {e}\n")
                    continue
                finally:
                    sys.stdout, sys.stderr = old_out, old_err
                # Append captured stdout/stderr
                printed = cap_out.getvalue()
                printed_err = cap_err.getvalue()
                if printed:
                    out_parts.append(printed)
                if printed_err:
                    out_parts.append(printed_err)
                # Append representation of return value
                if res is not None:
                    if want_raw:
                        payload = _normalize_raw(res)
                        if payload:
                            out_parts.append(payload if payload.endswith("\n") else payload + "\n")
                    else:
                        if isinstance(res, str):
                            if res != "":
                                out_parts.append(repr(res) + "\n")
                        else:
                            out_parts.append(repr(res) + "\n")
        return "".join(out_parts)

    reg.add_command("source", _source, "source [--raw] [--no-echo] <path> — execute each line from a text file")
