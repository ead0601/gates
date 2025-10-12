# REV:r4
# cmd_fanin.py — fanin with FULL path printing via --path (stops at ports/FFs unless requested)
from typing import List, Dict, Set, Tuple
import re
from registry import CommandRegistry
from core import Interpreter

SUMMARY = "fanin <target> [--endpoints] [--depth N] [--limit N] [--path]"
DETAIL = (
    "fanin <target> [--endpoints] [--depth N] [--limit N] [--path]\n"
    "  --endpoints   : print terminal sources only (one per line)\n"
    "  --depth N     : limit traversal depth (default 200)\n"
    "  --limit N     : limit number of sources/lines shown\n"
    "  --path        : print FULL path lines 'SOURCE : ... : TARGET'\n"
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
                return None, {"__raw":"fanin: --depth requires integer\n"}
            i += 2; continue
        if t == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i+1])
            except ValueError:
                return None, {"__raw":"fanin: --limit requires integer\n"}
            i += 2; continue
        return None, {"__raw": f"fanin: unknown option '{t}'\n"}
    return (target, depth, limit, endpoints_only, want_path), None

def _nodes_from_edges(edges: List[Dict[str,str]]):
    srcs: Set[str] = set(); dsts: Set[str] = set()
    for e in edges:
        s = e.get("src"); d = e.get("dst")
        if s: srcs.add(s)
        if d: dsts.add(d)
    return srcs, dsts

def _sources_from_edges(target: str, edges: List[Dict[str,str]]) -> List[str]:
    srcs, dsts = _nodes_from_edges(edges)
    nodes = srcs | dsts
    indeg = {n:0 for n in nodes}
    for e in edges:
        s = e.get("src"); d = e.get("dst")
        if s and d and d in indeg:
            indeg[d] += 1
    src_only = sorted([n for n in nodes if indeg.get(n,0) == 0 and n != target])
    return src_only

def _inst_name(pin: str) -> str:
    i = pin.rfind('.'); return pin[:i] if i > 0 else pin

def _is_pin(name: str) -> bool:
    return '.' in name

def _augment_with_intra_instance_reverse(edges: List[Dict[str,str]]):
    from collections import defaultdict
    radj = defaultdict(list)
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
        radj[d].append(s)
        indeg[s] = indeg.get(s,0) + 1
        indeg.setdefault(d, 0)
        if _is_pin(d) and not _is_pin(s):
            inst = _inst_name(d)
            pins_by_inst_inputs.setdefault(inst, set()).add(d)
            if _SEQ_PIN_RX.search(d): seq_inst.add(inst)
        if _is_pin(s) and not _is_pin(d):
            inst = _inst_name(s)
            pins_by_inst_outputs.setdefault(inst, set()).add(s)
            if _SEQ_PIN_RX.search(s): seq_inst.add(inst)
    for inst, out_pins in pins_by_inst_outputs.items():
        if inst in seq_inst:
            continue
        in_pins = pins_by_inst_inputs.get(inst, set())
        if not in_pins:
            continue
        for op in out_pins:
            for ip in in_pins:
                radj[ip].append(op)
                indeg[op] = indeg.get(op,0) + 1
                indeg.setdefault(ip, 0)
    return radj, indeg

def _bfs_path_forward(src: str, dst: str, radj):
    from collections import deque
    q = deque([dst]); parent = {dst: None}
    while q:
        u = q.popleft()
        if u == src:
            break
        for v in radj.get(u, ()):
            if v not in parent:
                parent[v] = u
                q.append(v)
    if src not in parent:
        return None
    seq = []
    x = src
    while x is not None:
        seq.append(x)
        x = parent[x]
    return seq

def _handler(args: List[str], interp: Interpreter):
    if not interp.trav:
        return {"__raw":"No graph loaded. Use: read verilog <manifest.lst>\n"}
    parsed, err = _parse(args)
    if err: return err
    target, depth, limit, endpoints_only, want_path = parsed
    net = target

    if hasattr(interp.trav, "fanin_cone"):
        nets_seen, insts_seen, edges = interp.trav.fanin_cone(net, depth=depth)
        if want_path:
            radj, indeg = _augment_with_intra_instance_reverse(edges)
            nodes = set(indeg.keys()) | set(radj.keys())
            indeg2 = {n:0 for n in nodes}
            for u, vs in radj.items():
                for v in vs:
                    indeg2[v] = indeg2.get(v,0) + 1
                    indeg2.setdefault(u, 0)
            sources = sorted([n for n,deg in indeg2.items() if deg == 0 and n != net])
            if limit is not None and limit >= 0:
                sources = sources[:limit]
            lines = []
            for s in sources:
                p = _bfs_path_forward(s, net, radj)
                if p:
                    lines.append(" : ".join(p))
            if not lines:
                return {"__raw":"(no paths)\n"}
            return {"__raw":"\n".join(lines) + "\n"}
        if endpoints_only:
            srcs = _sources_from_edges(net, edges)
            if limit is not None and limit >= 0:
                srcs = srcs[:limit]
            body = "".join(f"  - {s}\n" for s in srcs)
            return {"__raw": f"FANIN SOURCES for {target}\n" + body}
        return {
            "__raw": f"FANIN SUMMARY for {target}\n  nets={len(nets_seen)} insts={len(insts_seen)} edges={len(edges)}\n",
            "nets": sorted(nets_seen),
            "insts": sorted(list(insts_seen)),
            "edges": edges,
            "meta": {"direction": "in", "depth": depth, "stop": ["ff", "io", "const"]},
        }
    else:
        srcs = interp.trav.collect_fanin_endpoints(net, depth=depth)
        if want_path:
            if limit is not None and limit >= 0:
                srcs = srcs[:limit]
            lines = [f"{s} : {target}" for s in sorted(srcs)]
            return {"__raw":"\n".join(lines) + "\n"}
        if endpoints_only:
            if limit is not None and limit >= 0:
                srcs = srcs[:limit]
            body = "".join(f"  - {s}\n" for s in sorted(srcs))
            return {"__raw": f"FANIN SOURCES (fallback) for {target}\n" + body}
        body = "".join(f"  - {s}\n" for s in sorted(srcs))
        return {"__raw": f"FANIN SUMMARY for {target}\n(sources only; cone API unavailable)\n" + body}

def register(reg: CommandRegistry):
    reg.add_command("fanin", _handler, SUMMARY, DETAIL)
