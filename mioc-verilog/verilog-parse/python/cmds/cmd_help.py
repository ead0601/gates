# file: python/cmds/cmd_help.py
# note: Preserves old behavior for bare 'help' (delegates to registry.help_text()).
#       Adds 'help <name>' that prints the @help <name> block from the command's source.

from typing import List
import importlib, io, inspect
from registry import CommandRegistry

def _read_file(path: str) -> str:
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _extract_tag_block(src: str, tag: str, ident: str) -> str:
    lines = src.splitlines()
    out: List[str] = []
    start = None
    tag_header = f"# @{tag} {ident}".strip()
    for i, ln in enumerate(lines):
        if ln.strip() == tag_header:
            start = i + 1
            break
    if start is None:
        return ""
    for j in range(start, len(lines)):
        st = lines[j].strip()
        if not st.startswith("#"):
            break
        if st.startswith("# @"):  # next tag begins
            break
        if st.startswith("# "):
            out.append(st[2:])
        elif st == "#":
            out.append("")
        else:
            out.append(st[1:].lstrip())
    return "\n".join(out).rstrip()

def _get_handler_file(handler) -> str:
    try:
        return inspect.getsourcefile(handler) or inspect.getfile(handler) or ""
    except Exception:
        try:
            modname = getattr(handler, "__module__", None)
            if not modname:
                return ""
            mod = importlib.import_module(modname)
            return getattr(mod, "__file__", "") or ""
        except Exception:
            return ""

def _format_all_commands(reg: CommandRegistry) -> str:
    # Exact old behavior for bare 'help'
    return reg.help_text()

def _format_help_for(reg: CommandRegistry, name: str) -> str:
    # New behavior only for 'help <name>'
    handler = reg._cmds.get(name)
    if not handler:
        return f"Unknown command '{name}'. Type 'help' for a list of commands."
    src_path = _get_handler_file(handler)
    if src_path:
        src = _read_file(src_path)
        block = _extract_tag_block(src, "help", name)
        if block:
            return block
    # Fallback to the registry one-liner
    summ = reg._helps.get(name, "").strip()
    if summ:
        return f"{name} — {summ}"
    return f"(no help found for '{name}')"

def _handler(rest: str, interp) -> str:
    q = (rest or "").strip()
    if not q:
        return _format_all_commands(interp.registry)
    return _format_help_for(interp.registry, q.split()[0])

def register(reg: CommandRegistry) -> None:
    reg.register("help", _handler, "Show this help.")
