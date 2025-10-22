# === VNLT REV ===
# file: cmds/cmd_source.py
# rev:  2025-10-21 00:58  r4  tag:cmd
# note: source <file> — strip '#' comments; delegate to vnlt._dispatch_one; post-process vnlt._res_to_text if non-string
# === /VNLT REV ===

from pathlib import Path
from registry import CommandRegistry

from vnlt import _dispatch_one as _dispatch_one_vnlt
try:
    from vnlt import _res_to_text as _fmt_result
except Exception:
    _fmt_result = None

def _fallback_to_text(res) -> str:
    # Similar to REPL normalization
    if isinstance(res, str):
        return res
    if isinstance(res, dict):
        if "__raw" in res:
            return str(res.get("__raw") or "")
        if "text" in res:
            return str(res.get("text") or "")
        if "fields" in res:
            vals = res.get("fields") or []
            try:
                return ",".join(str(x) for x in vals)
            except Exception:
                return "\n".join(str(x) for x in vals)
    if res is None:
        return ""
    return str(res)

def _to_text(res) -> str:
    if _fmt_result:
        try:
            tmp = _fmt_result(res)
            return tmp if isinstance(tmp, str) else _fallback_to_text(tmp)
        except Exception:
            pass
    return _fallback_to_text(res)

def _handler(rest: str, interp) -> str:
    path = (rest or "").strip()
    if not path:
        return "usage: source <file>"
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    if not p.exists():
        return f"[source] file not found: {p}"

    out_lines = []
    for raw in p.read_text(errors="ignore").splitlines():
        cut = raw.split('#', 1)[0].strip()
        if not cut:
            continue
        try:
            res = _dispatch_one_vnlt(interp.registry, interp, cut)
            text = _to_text(res)
        except SystemExit:
            text = "[source] exit called; ignoring during batch"
        except Exception as e:
            text = f"[source] error: {e}"
        if text:
            out_lines.append(text.rstrip())
    return "\n".join(out_lines)

def register(reg: CommandRegistry) -> None:
    reg.register("source", _handler, "Run vnlt lines from a file (strip # comments).")
