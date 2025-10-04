# === VNLT REV ===
# file: python/cmd_fanout.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List
from registry import CommandRegistry
from core import Interpreter

def _handler(args: List[str], interp: Interpreter):
    if not interp.trav:
        return {"__raw":"No graph loaded. Use: read verilog <manifest.lst>\n"}
    endpoints_mode = False
    depth = 200
    tokens: List[str] = []
    it = iter(args)
    for a in it:
        if a == "--endpoints":
            endpoints_mode = True
        elif a == "--depth":
            depth = int(next(it))
        else:
            tokens.append(a)
    if not tokens:
        return {"__raw": DETAIL}
    target = tokens[0]
    net = interp.graph.resolve_target_to_net(target)
    if net is None:
        return {"cmd":"fanout","target":target,"error":{"code":"NOT_FOUND","msg":"target not found"}}
    if endpoints_mode:
        eps = interp.trav.collect_fanout_endpoints(net, depth=depth)
        if not eps:
            return {"__raw": f"FANOUT ENDPOINTS (TOP_OUT) for {target}\n  (none)\n"}
        lines = [f"FANOUT ENDPOINTS (TOP_OUT) for {target}"]
        for n in sorted(eps):
            lines.append(f"  - {interp.trav._display_net(n)}")
        return {"__raw":"\n".join(lines) + "\n"}
    nets, insts, edges = interp.trav.fanout_cone(net, depth=depth)
    return {
        "cmd":"fanout","target":target,"mode":"cone",
        "nodes":{"nets":sorted(nets),"instances":sorted(insts)},
        "edges":edges,
        "meta":{"direction":"out","depth":depth,"stop":["ff"]}
    }

SUMMARY = "fanout <target> [--endpoints] [--depth N]"
DETAIL = """\
Usage:
  fanout <target> [--endpoints] [--depth N]

Description:
  Explore what <target> drives (combinational only; does not cross FFs).
"""

def register(reg: CommandRegistry):
    reg.add_command("fanout", _handler, SUMMARY, DETAIL)
