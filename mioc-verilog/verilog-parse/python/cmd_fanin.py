# cmd_fanin.py — fanin explorer with built-in tree renderer (no core dependency)

from typing import List, Optional, Tuple
from registry import CommandRegistry
from core import Interpreter

SUMMARY = "fanin <target> [--tree|--endpoints] [--cross-ff] [--stage-limit N] [--depth N] [--branch N]"
DETAIL = """\
Usage:
  fanin <target> [--tree] [--endpoints] [--cross-ff] [--stage-limit N] [--depth N] [--branch N]

Description:
  Explore what drives <target>. <target> can be a pin (INST.PIN), a port (PORT:NAME),
  or a net (NET:NAME). Use --tree for an ASCII tree, --endpoints for TOP_IN/CONST list.
  By default, traversal stops at FF boundaries; add --cross-ff to walk through flops.
"""

def _resolve_target_net(tok: str, interp: Interpreter) -> Optional[str]:
    if not interp.graph:
        return None
    # Allow raw net names too: if resolution fails, we return None and the caller can try tok directly
    return interp.graph.resolve_target_to_net(tok)

def _render_fanin_tree(interp: Interpreter, start_net: str, *, depth: int, cross_ff: bool,
                       stage_limit: int, branch_limit: Optional[int]) -> str:
    """
    ASCII fan-in tree:
      • Stops at TOP_IN or CONST nets.
      • Stops at FF boundaries unless cross_ff=True.
      • depth: max edge depth (passed to summaries; used as overall guard here).
      • stage_limit: max gate levels to print (0 = unlimited).
      • branch_limit: max input pins to expand per gate (None = unlimited).
    """
    g = interp.graph
    t = interp.trav
    lines: List[str] = []
    seen_edges = set()
    seen_nets_depth = {start_net: 0}

    def is_ff(iname: str) -> bool:
        ctype = (g.instances.get(iname) or {}).get("type", "")
        return g.celllib.is_sequential(ctype) if g.celllib else False

    def emit(s: str, lvl: int):
        lines.append(("  " * lvl) + s)

    def walk_net(net: str, lvl: int, stages: int):
        if stage_limit > 0 and stages > stage_limit:
            emit("… (stage limit)", lvl)
            return
        curd = seen_nets_depth.get(net, lvl)
        if lvl > depth:
            emit("… (depth limit)", lvl)
            return
        if net in g.top_inputs:
            emit(f"{net} [TOP_IN]", lvl)
            return
        if getattr(g, "constants", None) and net in g.constants:
            emit(f"{net} [CONST]", lvl)
            return

        drivers = t._drivers_of(net)  # list[(iname, opin)]
        if not drivers:
            emit(f"{net} [NO_DRIVERS]", lvl)
            return

        # Expand each driver
        for (iname, opin) in drivers[: (branch_limit or 10**9)]:
            ctype = (g.instances.get(iname) or {}).get("type", "")
            emit(f"{iname}.{opin} [{ctype}]", lvl)
            # At FF boundary, stop unless cross_ff
            if is_ff(iname) and not cross_ff:
                emit("(ff boundary)", lvl + 1)
                continue
            # Walk each input pin of the driving instance
            count = 0
            for ipin, inet in t._inst_inputs(iname):
                edge_key = (inet, iname, ipin)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                emit(f"{iname}.{ipin}", lvl + 1)
                walk_net(inet, lvl + 2, stages + 1)
                count += 1
                if branch_limit and count >= branch_limit:
                    emit("… (branch limit)", lvl + 1)
                    break

    emit(f"FANIN TREE for {start_net}", 0)
    walk_net(start_net, 1, 0)
    return "\n".join(lines) + ("\n" if lines and not lines[-1].endswith("\n") else "")

def _handler(args: List[str], interp: Interpreter):
    if not interp.trav:
        return {"__raw": "No graph loaded. Use: read verilog <manifest.lst>\n"}

    tree_mode = False
    endpoints_mode = False
    cross_ff = False
    stage_limit = 0
    depth = 200
    branch_limit: Optional[int] = None
    tokens: List[str] = []
    it = iter(args)
    for a in it:
        if a == "--tree":
            tree_mode = True
        elif a == "--endpoints":
            endpoints_mode = True
        elif a == "--cross-ff":
            cross_ff = True
        elif a == "--stage-limit":
            stage_limit = int(next(it))
        elif a == "--depth":
            depth = int(next(it))
        elif a == "--branch":
            branch_limit = int(next(it))
        else:
            tokens.append(a)

    if not tokens:
        return {"__raw": DETAIL}
    target = tokens[0]

    # Resolve to a net if possible; if not, assume caller provided a raw net name
    net = _resolve_target_net(target, interp) or target

    if endpoints_mode:
        eps = interp.trav.collect_fanin_endpoints(net, depth=depth)
        body = "".join([f"  - {e}\n" for e in sorted(eps)])
        return {"__raw": f"FANIN ENDPOINTS (TOP_IN/CONST) for {target}\n" + body}

    if tree_mode:
        text = _render_fanin_tree(interp, net, depth=depth, cross_ff=cross_ff,
                                  stage_limit=stage_limit, branch_limit=branch_limit)
        return {"__raw": text}

    # Default summary mode (cone sizes)
    if hasattr(interp.trav, "fanin_cone"):
        nets_seen, insts_seen, edges = interp.trav.fanin_cone(net, depth=depth)
        return {
            "__raw": f"FANIN SUMMARY for {target}\n  nets={len(nets_seen)} insts={len(insts_seen)} edges={len(edges)}\n",
            "nets": sorted(nets_seen),
            "insts": sorted(list(insts_seen)),
            "edges": edges,
            "meta": {"direction": "in", "depth": depth, "stop": ["ff", "io", "const"]},
        }
    else:
        # Fallback: just run endpoints mode if cone summary not available
        eps = interp.trav.collect_fanin_endpoints(net, depth=depth)
        body = "".join([f"  - {e}\n" for e in sorted(eps)])
        return {"__raw": f"FANIN ENDPOINTS (fallback) for {target}\n" + body}

def register(reg: CommandRegistry):
    reg.add_command("fanin", _handler, SUMMARY, DETAIL)
