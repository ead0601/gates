
from typing import List
from registry import CommandRegistry
from core import Interpreter
import fnmatch

SUMMARY = "find <components|instance|pin|port|net> PATTERN — wildcard search"
DETAIL = """\
Usage:
  find components PATTERN
  find instance PATTERN
  find pin PATTERN         # e.g., U2*.A
  find port PATTERN
  find net PATTERN

Notes:
  - PATTERN supports globs (* ? [abc]). Case-sensitive.
  - Default output is one match per line; add --long for descriptors.
"""

def _handler(args: List[str], interp: Interpreter):
    if not args or len(args) < 2:
        return {"__raw": DETAIL}
    kind, pattern, *rest = args
    want_long = ("--long" in rest)
    out = []
    if not interp.graph and kind != "components":
        return {"__raw": "No design loaded.\n"}
    if kind == "components":
        if not interp.celllib:
            return {"__raw":"No design loaded.\n"}
        for c in sorted(interp.celllib.pin_dir.keys()):
            if fnmatch.fnmatch(c, pattern):
                out.append(c if not want_long else f"{c} ({'seq' if interp.celllib.is_sequential(c) else 'comb'})")
    elif kind == "instance":
        for iname, inst in sorted(interp.graph.instances.items()):
            if fnmatch.fnmatch(iname, pattern):
                t = inst.get("type","")
                out.append(iname if not want_long else f"{iname} ({t})")
    elif kind == "pin":
        for iname, inst in interp.graph.instances.items():
            for pin in (inst.get('pins') or {}).keys():
                ip = f"{iname}.{pin}"
                if fnmatch.fnmatch(ip, pattern):
                    net = (inst.get('pins') or {}).get(pin, "")
                    out.append(ip if not want_long else f"{ip} -> {net}")
        out.sort()
    elif kind == "port":
        for p in sorted(set(list(interp.graph.top_inputs) + list(interp.graph.top_outputs))):
            if fnmatch.fnmatch(p, pattern):
                out.append(p)
    elif kind == "net":
        for n in sorted(interp.graph.nets.keys()):
            if fnmatch.fnmatch(n, pattern):
                out.append(n)
    else:
        return {"__raw": DETAIL}
    if not out:
        return {"__raw": "No matches.\n"}
    return {"__raw": "\n".join(out) + "\n"}

def register(reg: CommandRegistry):
    reg.add_command("find", _handler, SUMMARY, DETAIL)
