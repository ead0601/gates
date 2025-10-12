# REV:r4
# cmd_fanout.py — fanout with FULL path printing via --path (stops at ports/FFs unless requested)
from typing import List, Dict, Set, Tuple
import re
from registry import CommandRegistry
from core import Interpreter

SUMMARY = "fanout <target> [--endpoints] [--depth N] [--limit N] [--path]"
DETAIL = (
    "fanout <target> [--endpoints] [--depth N] [--limit N] [--path]\n"
    "  --endpoints   : print terminal sinks only (one per line)\n"
    "  --depth N     : limit traversal depth (default 200)\n"
    "  --limit N     : limit number of endpoints/lines shown\n"
    "  --path        : print FULL path lines 'SRC : ... : ENDPOINT'\n"
)

_SEQ_PIN_RX = re.compile(r"\.(D|Q|CLK|CLKN|RN|SN)\b", re.IGNORECASE)

def _parse(args: List[str]):
    if not args:
        return None, {"__raw": "Usage: " + SUMMARY + "\n"}
    target = args[0]
    depth = 200
    limit = None
    endpoints_only = False
    want_path = False
    i = 1
    while i < len(args):
        t = args[i]
        if t == "--endpoints":
            endpoints_only = True; i += 1; continue
        if t == "--path":
            want_path = True; i += 1; continue
        if t == "--depth" and i + 1 < len(args):
            try:
                depth = int(args[i+1])
            except ValueError:
                return None, {"__raw":"fanout: --depth requires integer\n"}
            i += 2; continue
        if t == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i+1])
            except ValueError:
                return None, {"__raw":"fanout: --limit requires integer\n"}
            i += 2; continue
        return None, {"__raw": f"fanout: unknown option '{t}'\n"}
    return (target, depth, limit, endpoints_only, want_path), None

def _nodes_from_edges(edges: List[Dict[str,str]]) -> Tuple[Set[str], Set[str]]:
    srcs: Set[str] = set(); dsts: Set[str] = set()
    for e in edges:
        s = e.get("src"); d = e.get("dst")
        if s: srcs.add(s)
        if d: dsts.add(d)
    return srcs, dsts

def _endpoints_from_edges(target: str, edges: List[Dict[str,str]]) -> List[str]:
    srcs, dsts = _nodes_from_edges(edges)
    nodes = srcs | dsts
    outdeg = {n:0 for n in nodes}
    for e in edges:
        s = e.get("src"); d = e.get("dst")
        if s and d and s in outdeg:
            outdeg[s] += 1
    eps = sorted([n for n in nodes if outdeg.get(n,0) == 0 and n != target])
    return eps

def _inst_name(pin: str) -> str:
    i = pin.rfind('.')
    return pin[:i] if i > 0 else pin

def _is_pin(name: str) -> bool:
    return '.' in name

def _augment_with_intra_instance(edges: List[Dict[str,str]]):
    from collections import defaultdict
    adj = defaultdict(list)
    indeg = {}
    pins_by_inst_inputs = {}
    pins_by_inst_outputs = {}
    seq_inst: Set[str] = set()
    nodes: Set[str] = set()
    for e in edges:
        s = e.get("src"); d = e.get("dst")
        if not s or not d: 
            continue
        nodes.add(s); nodes.add(d)
        adj[s].append(d)
        indeg[d] = indeg.get(d,0) + 1
        indeg.setdefault(s, 0)
        if _is_pin(d) and not _is_pin(s):
            inst = _inst_name(d)
            pins_by_inst_inputs.setdefault(inst, set()).add(d)
            if _SEQ_PIN_RX.search(d): seq_inst.add(inst)
        if _is_pin(s) and not _is_pin(d):
            inst = _inst_name(s)
            pins_by_inst_outputs.setdefault(inst, set()).add(s)
            if _SEQ_PIN_RX.search(s): seq_inst.add(inst)
    for inst, in_pins in pins_by_inst_inputs.items():
        if inst in seq_inst:
            continue
        out_pins = pins_by_inst_outputs.get(inst, set())
        if not out_pins:
            continue
        for ip in in_pins:
            for op in out_pins:
                adj[ip].append(op)
                indeg[op] = indeg.get(op,0) + 1
                indeg.setdefault(ip, 0)
    return adj, indeg

def _bfs_path(src: str, dst: str, adj):
    from collections import deque
    q = deque([src]); parent = {src: None}
    while q:
        u = q.popleft()
        if u == dst:
            break
        for v in adj.get(u, ()):
            if v not in parent:
                parent[v] = u
                q.append(v)
    if dst not in parent:
        return None
    path = []
    x = dst
    while x is not None:
        path.append(x)
        x = parent[x]
    path.reverse()
    return path

def _handler(args: List[str], interp: Interpreter):
    if not interp.trav:
        return {"__raw":"No graph loaded. Use: read verilog <manifest.lst>\n"}
    parsed, err = _parse(args)
    if err: return err
    target, depth, limit, endpoints_only, want_path = parsed
    net = target

    if hasattr(interp.trav, "fanout_cone"):
        nets, insts, edges = interp.trav.fanout_cone(net, depth=depth)
        if want_path:
            adj, indeg = _augment_with_intra_instance(edges)
            outdeg = {n:0 for n in set(list(indeg.keys()) + list(adj.keys()))}
            for u, vs in adj.items():
                if not vs:
                    outdeg.setdefault(u, 0)
                for v in vs:
                    outdeg[u] = outdeg.get(u,0) + 1
                    outdeg.setdefault(v, 0)
            endpoints = sorted([n for n,deg in outdeg.items() if deg == 0 and n != net])
            if limit is not None and limit >= 0:
                endpoints = endpoints[:limit]
            lines = []
            for ep in endpoints:
                p = _bfs_path(net, ep, adj)
                if p:
                    lines.append(" : ".join(p))
            if not lines:
                return {"__raw":"(no paths)\n"}
            return {"__raw":"\n".join(lines) + "\n"}
        if endpoints_only:
            eps = _endpoints_from_edges(net, edges)
            if limit is not None and limit >= 0:
                eps = eps[:limit]
            body = "".join(f"  - {e}\n" for e in eps)
            return {"__raw": f"FANOUT ENDPOINTS for {target}\n" + body}
        return {
            "cmd":"fanout",
            "target": target,
            "mode": "cone",
            "nodes": {"nets":sorted(nets), "instances":sorted(insts)},
            "edges": edges,
            "meta": {"direction":"out","depth":depth,"stop":["ff"]},
        }
    else:
        eps = interp.trav.collect_fanout_endpoints(net, depth=depth)
        if want_path:
            if limit is not None and limit >= 0:
                eps = eps[:limit]
            lines = [f"{target} : {e}" for e in sorted(eps)]
            return {"__raw":"\n".join(lines) + "\n"}
        if endpoints_only:
            if limit is not None and limit >= 0:
                eps = eps[:limit]
            body = "".join(f"  - {e}\n" for e in sorted(eps))
            return {"__raw": f"FANOUT ENDPOINTS (fallback) for {target}\n" + body}
        body = "".join(f"  - {e}\n" for e in sorted(eps))
        return {"__raw": f"FANOUT SUMMARY for {target}\n(endpoints only; cone API unavailable)\n" + body}

def register(reg: CommandRegistry):
    reg.add_command("fanout", _handler, SUMMARY, DETAIL)
