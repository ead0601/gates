# === VNLT REV ===
# file: cmds/cmd_find.py
# rev:  2025-10-20 23:14  r8  tag:cmd
# note: Unified list/path/fanin/fanout with robust net connection normalization (str/tuple/dict). Fixes tuple split crash.
# === /VNLT REV ===

import fnmatch, collections
from typing import Dict, List, Tuple, Iterable, Set, Callable, Optional
from registry import CommandRegistry

# -----------------------------
# Helpers: graph access & normalize
# -----------------------------

def _cell_is_sequential(interp, inst_name: str) -> bool:
    # Try common APIs; default to False if unknown.
    inst = (interp.graph.instances or {}).get(inst_name) or {}
    ctype = inst.get('type') or inst.get('cell') or inst.get('module') or ''
    cl = getattr(interp, 'celllib', None)
    for attr in ('is_sequential','is_sequential_type','is_seq','is_seq_type'):
        fn = getattr(cl, attr, None)
        if callable(fn):
            try:
                return bool(fn(ctype))
            except Exception:
                pass
    # Heuristics via celllib data
    cells = getattr(cl, 'cells', None)
    if isinstance(cells, dict):
        meta = cells.get(ctype) or {}
        cat = (meta.get('category') or meta.get('cat') or '').lower()
        if cat in ('seq','sequential','flop','ff','latch'):
            return True
    return False

def _norm_conn(x) -> Tuple[str, str]:
    """Normalize a connection into (inst, pin).
    Accepts: 'u1.A', ('u1','A'), {'inst':'u1','pin':'A'}
    """
    if isinstance(x, tuple) and len(x)==2:
        a,b = x
        return str(a), str(b)
    if isinstance(x, dict):
        a = x.get('inst') or x.get('instance') or x.get('name') or x.get('i') or ''
        b = x.get('pin') or x.get('p') or ''
        return str(a), str(b)
    s = str(x)
    if '.' in s:
        a,b = s.split('.',1); return a,b
    return s,''

def _index_net_to_insts(interp) -> Dict[str, Set[str]]:
    idx: Dict[str, Set[str]] = collections.defaultdict(set)
    nets = getattr(interp.graph, 'nets', {}) or {}
    for net, rec in nets.items():
        if not isinstance(rec, dict): 
            continue
        for side in ('drivers','loads'):
            for x in (rec.get(side) or []):
                inst, _ = _norm_conn(x)
                if inst:
                    idx[net].add(inst)
    return idx

def _nets_to_insts(interp, net: str) -> List[str]:
    return sorted(_index_net_to_insts(interp).get(net, []))

def _inst_to_nets(interp, inst: str) -> Tuple[List[str], List[str]]:
    """Return (input_nets, output_nets) for inst if available; else all connected nets as outputs."""
    inst_rec = (interp.graph.instances or {}).get(inst) or {}
    pins = inst_rec.get('pins') or {}
    ins, outs = [], []
    for pin, net in pins.items():
        # Try to infer direction: check celllib if available
        dirn = None
        cl = getattr(interp, 'celllib', None)
        if cl and hasattr(cl, 'pin_dir_of'):
            try:
                dirn = cl.pin_dir_of(inst_rec.get('type',''), pin)
            except Exception:
                dirn = None
        (outs if dirn=='out' else ins if dirn=='in' else outs).append(net)
    # Fallback if empty: via net index
    if not (ins or outs):
        idx = _index_net_to_insts(interp)
        for n, insts in idx.items():
            if inst in insts:
                outs.append(n)
    return (sorted(set(ins)), sorted(set(outs)))

# -----------------------------
# Parsing & matching
# -----------------------------

def _parse_args(rest: str):
    toks = [t for t in (rest or '').split() if t.strip()]
    src = None; dst = None; tree = False; cross = False
    i=0
    while i < len(toks):
        t = toks[i]
        if t == '-src' and i+1 < len(toks):
            src = toks[i+1]; i+=2; continue
        if t == '-dst' and i+1 < len(toks):
            dst = toks[i+1]; i+=2; continue
        if t == '-tree':
            tree = True; i+=1; continue
        if t == '-cross_sync':
            cross = True; i+=1; continue
        i+=1
    return src, dst, cross, tree

def _kind_and_glob(s: str) -> Tuple[str, str]:
    if not s: return '', ''
    if s.startswith('inst.'): return 'inst', s[5:]
    if s.startswith('net.'):  return 'net',  s[4:]
    if s.startswith('iport.'):return 'iport',s[6:]
    if s.startswith('oport.'):return 'oport',s[6:]
    # default to inst.* for convenience
    return 'inst', s

def _match_set(names: Iterable[str], pat: str) -> List[str]:
    if not pat or pat == '*': return sorted(set(names))
    return sorted({n for n in names if fnmatch.fnmatch(n, pat)})

# -----------------------------
# Path search
# -----------------------------

def _neighbors_from_net(interp, net: str) -> List[Tuple[str,str]]:
    return [('inst', i) for i in _nets_to_insts(interp, net)]

def _neighbors_from_inst(interp, inst: str, allow_cross: bool) -> List[Tuple[str,str]]:
    # From inst -> nets (usually outputs first, then loads)
    if (not allow_cross) and _cell_is_sequential(interp, inst):
        return []  # do not cross sync elements
    ins, outs = _inst_to_nets(interp, inst)
    # Traverse outward via outputs primarily; include inputs to allow walking back to nets
    nbrs: List[Tuple[str,str]] = []
    for n in outs: nbrs.append(('net', n))
    for n in ins:  nbrs.append(('net', n))
    return nbrs

def _dfs_all_paths(interp, src_nodes: List[Tuple[str,str]], dst_pred: Callable[[Tuple[str,str]], bool], allow_cross: bool, max_nodes: int = 20000) -> List[List[Tuple[str,str]]]:
    seen = set(); paths: List[List[Tuple[str,str]]] = []
    def dfs(node: Tuple[str,str], path: List[Tuple[str,str]]):
        if len(seen) > max_nodes: return
        if dst_pred(node):
            paths.append(path[:]); return
        seen.add(node)
        t,v = node
        nbrs = _neighbors_from_net(interp, v) if t=='net' else _neighbors_from_inst(interp, v, allow_cross)
        for nxt in nbrs:
            if nxt in path: 
                continue
            path.append(nxt); dfs(nxt, path); path.pop()
    for s in src_nodes:
        dfs(s, [s])
    return paths

# -----------------------------
# Rendering
# -----------------------------

def _fmt_node(node: Tuple[str,str]) -> str:
    t,v = node
    return f"{t}.{v}"

def _render_path(path: List[Tuple[str,str]]) -> str:
    return " : ".join(_fmt_node(n) for n in path)

def _render_tree(paths: List[List[Tuple[str,str]]]) -> str:
    # Build a simple prefix tree by string form
    root = {}
    for p in paths:
        parts = [_fmt_node(n) for n in p]
        cur = root
        for part in parts:
            cur = cur.setdefault(part, {})
        cur.setdefault('__end__', True)

    lines: List[str] = []
    def walk(node: Dict, prefix: str = ""):
        keys = [k for k in node.keys() if k != '__end__']
        for i, k in enumerate(sorted(keys)):
            last = (i == len(keys)-1)
            branch = "└─ " if last else "├─ "
            lines.append(prefix + branch + k)
            walk(node[k], prefix + ("   " if last else "│  "))
    walk(root)
    return "\n".join(lines)

# -----------------------------
# Core handler
# -----------------------------

# @help find
# find — unified listing & path search
#
# Usage:
#   # Listing mode (names only)
#   find -src <inst.* | net.* | iport.* | oport.*>
#
#   # Path search (walk graph from sources to a destination)
#   find -src <inst.* | net.*> -dst <inst.* | net.* | iport.* | oport.*> [-cross_sync] [-tree]
#
# Kinds:
#   inst.<glob>   instance names (default kind if prefix omitted)
#   net.<glob>    net names
#   iport.<glob>  top-level input ports
#   oport.<glob>  top-level output ports
#
# Glob patterns:
#   *  ?  [abc]  [a-z]  — standard shell-style matching.
#
# Flags:
#   -cross_sync   allow traversal through sequential cells (by default, paths do NOT cross flops/latches)
#   -tree         render all found paths as a prefix tree (nice for fanout/fanin exploration)
#
# Behavior:
#   • Listing mode (only -src given) prints matching names, one per line.
#   • Path search builds a mixed graph (inst↔net). It starts from all -src matches and stops
#     when a node matches -dst. Paths do not cross sequential cells unless -cross_sync is set.
#   • Destination kind can be inst, net, iport, or oport. iport/oport match when the path lands on a net
#     that is a top-level input/output net.
#
# Examples:
#   # List instances / nets / top ports
#   find -src inst.u*             # all instances starting with "u"
#   find -src net.clk_*           # all nets matching clk_*
#   find -src iport.*             # all top inputs
#   find -src oport.*             # all top outputs
#
#   # Paths between instances
#   find -src inst.uA* -dst inst.uB*          # any path from uA* to uB* (no crossing flops)
#   find -src inst.uA   -dst inst.uB -cross_sync
#
#   # From instance(s) to top-level outputs
#   find -src inst.core/* -dst oport.*        # which outputs are reachable from core/*
#
#   # From top-level inputs (as nets) into instances
#   find -src net.reset_n -dst inst.u_sync/*
#
#   # Render a tree of all paths
#   find -src inst.uA -dst oport.* -tree
#
# Notes:
#   • For path search, -src must be inst.* or net.* (ports aren’t valid sources).
#   • iport/oport destinations hit when the current node is a net that is in the design’s top inputs/outputs.
#   • The tree view prints a compact prefix tree of all path strings.
#
def _handler(rest: str, interp) -> str:
    src, dst, cross, tree = _parse_args(rest)

    # Simple listings
    if src and not dst:
        k, pat = _kind_and_glob(src)
        if k == 'inst':
            names = list((interp.graph.instances or {}).keys())
            return "\n".join(_match_set(names, pat))
        elif k == 'net':
            names = list((interp.graph.nets or {}).keys())
            return "\n".join(_match_set(names, pat))
        elif k in ('iport','oport'):
            if k=='iport':
                names = list((interp.graph.top_inputs or set()) or [])
            else:
                names = list((interp.graph.top_outputs or set()) or [])
            return "\n".join(_match_set(names, pat))
        return "usage: find -src <inst.*|net.*|iport.*|oport.*> [-dst <...>] [-cross_sync] [-tree]"

    # Path search mode
    if not (src and dst):
        return "usage: find -src <kind.pattern> -dst <kind.pattern> [-cross_sync] [-tree]"

    skind, spat = _kind_and_glob(src)
    dkind, dpat = _kind_and_glob(dst)

    # Build src node set
    if skind == 'inst':
        s_candidates = _match_set((interp.graph.instances or {}).keys(), spat)
        src_nodes = [('inst', n) for n in s_candidates]
    elif skind == 'net':
        s_candidates = _match_set((interp.graph.nets or {}).keys(), spat)
        src_nodes = [('net', n) for n in s_candidates]
    else:
        return "Only inst.* or net.* supported for -src"

    # Destination predicate
    def _dst_pred(node: Tuple[str,str]) -> bool:
        t,v = node
        if dkind == 'inst' and t == 'inst':
            return fnmatch.fnmatch(v, dpat)
        if dkind == 'net' and t == 'net':
            return fnmatch.fnmatch(v, dpat)
        if dkind == 'iport' and t == 'net':
            return v in (interp.graph.top_inputs or set())
        if dkind == 'oport' and t == 'net':
            return v in (interp.graph.top_outputs or set())
        return False

    paths = _dfs_all_paths(interp, src_nodes, _dst_pred, allow_cross=cross)

    if not paths:
        return ""

    if tree:
        return _render_tree(paths)
    return "\n".join(_render_path(p) for p in paths)

def register(reg: CommandRegistry):
    reg.register("find", _handler, "Unified list/path/fanin/fanout; -src/-dst/-cross_sync/-tree")
