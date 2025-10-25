# === VNLT REV ===
# file: cmds/cmd_find.py
# rev:  2025-10-25  r15  tag:cmd
# note: Directional traversal using net driver/load index (no pin-dir guess).
#       -back (fanin), -max_nodes/-max_paths/-max_depth, virtual kinds (seq./gate.),
#       inst.<type>.<name> sugar, iport./oport. as src/dst, -type filters.
#       -label_types → inst.NAME[TYPE] (fallback [SEQ]).
#       NEW: -show_stops → when no full path reaches -dst, also render partial paths
#            to the first stop point, annotated with STOP:seq | STOP:depth | STOP:dead.
# === /VNLT REV ===

import os, fnmatch, collections
from typing import Dict, List, Tuple, Iterable, Set, Callable, Optional
from registry import CommandRegistry

# -----------------------------
# Helpers: graph access & normalize
# -----------------------------

def _cell_type_of(interp, inst_name: str) -> str:
    inst = (interp.graph.instances or {}).get(inst_name) or {}
    return inst.get('type') or inst.get('cell') or inst.get('module') or ''

def _cell_is_sequential(interp, inst_name: str) -> bool:
    """Return True if instance's cell type is sequential (flop/latch)."""
    ctype = _cell_type_of(interp, inst_name)
    cl = getattr(interp, 'celllib', None)
    for attr in ('is_sequential','is_sequential_type','is_seq','is_seq_type'):
        fn = getattr(cl, attr, None)
        if callable(fn):
            try:
                return bool(fn(ctype))
            except Exception:
                pass
    cells = getattr(cl, 'cells', None)
    if isinstance(cells, dict):
        meta = cells.get(ctype) or {}
        cat = (meta.get('category') or meta.get('cat') or '').lower()
        if cat in ('seq','sequential','flop','ff','latch'):
            return True
        pins = meta.get('pins') or {}
        if {'D','Q','CLK'} & set(map(str.upper, pins.keys())):
            return True
    u = ctype.lower()
    return any(k in u for k in ('dff','ff','flop','reg','qreg','latch'))

def _norm_conn(x) -> Tuple[str, str]:
    """Normalize edge endpoint representation into (inst, pin)."""
    if isinstance(x, tuple) and len(x)==2:
        a,b = x; return str(a), str(b)
    if isinstance(x, dict):
        a = x.get('inst') or x.get('instance') or x.get('name') or x.get('i') or ''
        b = x.get('pin') or x.get('p') or ''
        return str(a), str(b)
    s = str(x)
    if '.' in s:
        a,b = s.split('.',1); return a,b
    return s,''

def _index_net_sides(interp) -> Dict[str, Dict[str, Set[str]]]:
    """
    idx[net] = {'drivers': set(inst), 'loads': set(inst)}
    """
    idx: Dict[str, Dict[str, Set[str]]] = collections.defaultdict(lambda: {'drivers': set(), 'loads': set()})
    nets = getattr(interp.graph, 'nets', {}) or {}
    for net, rec in nets.items():
        if not isinstance(rec, dict):
            continue
        for x in (rec.get('drivers') or []):
            inst, _ = _norm_conn(x)
            if inst: idx[net]['drivers'].add(inst)
        for x in (rec.get('loads') or []):
            inst, _ = _norm_conn(x)
            if inst: idx[net]['loads'].add(inst)
    return idx

def _nets_to_load_insts(idx, net: str) -> List[str]:
    return sorted(idx.get(net, {}).get('loads', set()))

def _nets_to_driver_insts(idx, net: str) -> List[str]:
    return sorted(idx.get(net, {}).get('drivers', set()))

def _inst_inputs_outputs_from_index(idx, inst: str) -> Tuple[List[str], List[str]]:
    """(input_nets, output_nets) purely from driver/load index."""
    ins, outs = set(), set()
    for net, sides in idx.items():
        if inst in sides['loads']:
            ins.add(net)
        if inst in sides['drivers']:
            outs.add(net)
    return sorted(ins), sorted(outs)

# -----------------------------
# Parsing & matching
# -----------------------------

def _parse_args(rest: str):
    """
    Return: (src, dst, cross, tree, type_globs, max_nodes, max_paths, max_depth, back, label_types, show_stops)
    """
    toks = [t for t in (rest or '').split() if t.strip()]
    src = None; dst = None; tree = False; cross = False; type_globs: List[str] = []
    max_nodes = None; max_paths = None; max_depth = None; back = False; label_types = False; show_stops = False
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
        if t == '-type' and i+1 < len(toks):
            type_globs.append(toks[i+1]); i+=2; continue
        if t == '-max_nodes' and i+1 < len(toks):
            try: max_nodes = int(toks[i+1])
            except: max_nodes = None
            i+=2; continue
        if t == '-max_paths' and i+1 < len(toks):
            try: max_paths = int(toks[i+1])
            except: max_paths = None
            i+=2; continue
        if t == '-max_depth' and i+1 < len(toks):
            try: max_depth = int(toks[i+1])
            except: max_depth = None
            i+=2; continue
        if t == '-back':
            back = True; i+=1; continue
        if t == '-label_types':
            label_types = True; i+=1; continue
        if t == '-show_stops':
            show_stops = True; i+=1; continue
        i+=1
    return src, dst, cross, tree, type_globs, max_nodes, max_paths, max_depth, back, label_types, show_stops

def _kind_and_glob(s: str) -> Tuple[str, str]:
    """Return (kind, pattern). Kind ∈ {'inst','net','iport','oport','seq','gate'}."""
    if not s: return '', ''
    if s.startswith('inst.'): return 'inst', s[5:]
    if s.startswith('net.'):  return 'net',  s[4:]
    if s.startswith('iport.'):return 'iport',s[6:]
    if s.startswith('oport.'):return 'oport',s[6:]
    if s.startswith('seq.'):  return 'seq',  s[4:]
    if s.startswith('gate.'): return 'gate', s[5:]
    return 'inst', s  # default

def _split_inst_type_sugar(pat: str) -> Tuple[Optional[str], str]:
    """inst.<typeglob>.<nameglob> sugar."""
    if not pat: return None, ''
    if '.' not in pat:
        return None, pat
    tpat, npat = pat.split('.', 1)
    return (tpat or None), (npat or '*')

def _match_set(names: Iterable[str], pat: str) -> List[str]:
    if not pat or pat == '*': return sorted(set(names))
    return sorted({n for n in names if fnmatch.fnmatch(n, pat)})

def _type_matches(interp, inst_name: str, type_globs: List[str]) -> bool:
    if not type_globs:
        return True
    ctype = _cell_type_of(interp, inst_name)
    return any(fnmatch.fnmatch(ctype, g) for g in type_globs)

# -----------------------------
# Directional neighbors (using net index)
# -----------------------------

def _neighbors_from_net_forward(idx, net: str) -> List[Tuple[str,str]]:
    return [('inst', i) for i in _nets_to_load_insts(idx, net)]  # net → LOAD insts

def _neighbors_from_net_back(idx, net: str) -> List[Tuple[str,str]]:
    return [('inst', i) for i in _nets_to_driver_insts(idx, net)]  # net → DRIVER insts

def _neighbors_from_inst_forward(idx, interp, inst: str, allow_cross: bool) -> List[Tuple[str,str]]:
    if (not allow_cross) and _cell_is_sequential(interp, inst):
        return []  # seq boundary
    _ins, outs = _inst_inputs_outputs_from_index(idx, inst)
    return [('net', n) for n in outs]

def _neighbors_from_inst_back(idx, interp, inst: str, allow_cross: bool) -> List[Tuple[str,str]]:
    if (not allow_cross) and _cell_is_sequential(interp, inst):
        return []  # seq boundary
    ins, _outs = _inst_inputs_outputs_from_index(idx, inst)
    return [('net', n) for n in ins]

# -----------------------------
# Bounded DFS (with stop capture)
# -----------------------------

def _dfs_all_paths(interp, idx,
                   src_nodes: List[Tuple[str,str]],
                   dst_pred: Callable[[Tuple[str,str]], bool],
                   allow_cross: bool,
                   forward: bool,
                   max_nodes: Optional[int] = None,
                   max_paths: Optional[int] = None,
                   max_depth: Optional[int] = None,
                   collect_stops: bool = False) -> Tuple[List[List[Tuple[str,str]]], bool, List[List[Tuple[str,str]]], List[str]]:
    """
    Return (paths, truncated_flag, stop_paths, stop_reasons).
    When collect_stops=True, capture partial paths that end due to:
      - sequential boundary (no crossing): reason 'seq'
      - max_depth exceeded:                reason 'depth'
      - no neighbors (dead end):           reason 'dead'
    """
    if max_nodes is None:
        max_nodes = int(os.getenv("FIND_MAX_NODES", "20000") or "20000")
    if max_paths is None:
        max_paths = int(os.getenv("FIND_MAX_PATHS", "2000") or "2000")

    visited_count = 0
    out_paths: List[List[Tuple[str,str]] ] = []
    stop_paths: List[List[Tuple[str,str]]] = []
    stop_reasons: List[str] = []
    truncated = False

    def _push_stop(path: List[Tuple[str,str]], reason: str):
        if collect_stops and path:
            stop_paths.append(path[:])
            stop_reasons.append(reason)

    def dfs(node: Tuple[str,str], path: List[Tuple[str,str]]):
        nonlocal visited_count, truncated
        if truncated:
            return
        if visited_count >= max_nodes:
            truncated = True
            return
        if len(out_paths) >= max_paths:
            truncated = True
            return

        # Depth check (edges = len(path)-1)
        if (max_depth is not None) and (len(path) - 1 >= max_depth):
            _push_stop(path, 'depth')
            return

        visited_count += 1
        if dst_pred(node):
            out_paths.append(path[:])
            return

        t,v = node
        if forward:
            nbrs = (_neighbors_from_net_forward(idx, v) if t=='net'
                    else _neighbors_from_inst_forward(idx, interp, v, allow_cross))
        else:
            # If we are at an inst and it's sequential while crossing is off, this is a stop.
            if t=='inst' and (not allow_cross) and _cell_is_sequential(interp, v):
                _push_stop(path, 'seq')
                return
            nbrs = (_neighbors_from_net_back(idx, v) if t=='net'
                    else _neighbors_from_inst_back(idx, interp, v, allow_cross))

        if not nbrs:
            _push_stop(path, 'dead')
            return

        for nxt in nbrs:
            if nxt in path:
                continue
            path.append(nxt)
            dfs(nxt, path)
            path.pop()

    for s in src_nodes:
        if truncated or len(out_paths) >= max_paths:
            break
        dfs(s, [s])

    return out_paths, truncated, stop_paths, stop_reasons

# -----------------------------
# Rendering
# -----------------------------

def _make_fmt(interp, label_types: bool):
    def _fmt_node(node: Tuple[str,str]) -> str:
        t,v = node
        if t != 'inst' or not label_types:
            return f"{t}.{v}"
        ctype = _cell_type_of(interp, v)
        if not ctype and _cell_is_sequential(interp, v):
            ctype = "SEQ"
        return f"{t}.{v}[{ctype}]" if ctype else f"{t}.{v}"
    return _fmt_node

def _render_path(paths: List[List[Tuple[str,str]]], fmt_node, stop_reasons: Optional[List[str]] = None) -> str:
    lines = []
    if stop_reasons is None:
        for p in paths:
            lines.append(" : ".join(fmt_node(n) for n in p))
    else:
        # parallel arrays: paths[i] has stop_reasons[i]
        for p, reason in zip(paths, stop_reasons):
            if p:
                s = " : ".join(fmt_node(n) for n in p[:-1])
                last = fmt_node(p[-1]) + f" [STOP:{reason}]"
                lines.append((s + " : " if s else "") + last)
    return "\n".join(lines)

def _render_tree(paths: List[List[Tuple[str,str]]], fmt_node) -> str:
    root = {}
    for p in paths:
        parts = [fmt_node(n) for n in p]
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
# find — unified listing & path search (type filters, virtual kinds, direction, and labels)
#
# Usage:
#   # Listing mode (names only)
#   find -src <inst.* | net.* | iport.* | oport.* | seq.* | gate.*> [-type <glob>]... [-label_types]
#
#   # Path search (walk graph from sources to a destination)
#   # Forward fanout (default) or backward fanin (-back):
#   find -src <inst.*|net.*|iport.*|oport.*|seq.*|gate.*> \
#        -dst <inst.*|net.*|iport.*|oport.*|seq.*|gate.*> \
#        [-type <glob>]... [-cross_sync] [-tree] [-max_nodes N] [-max_paths N] [-max_depth N] \
#        [-back] [-label_types] [-show_stops]
#
# Kinds (sources/dests):
#   inst.<glob>           instance names (default kind if prefix omitted)
#   net.<glob>            net names
#   iport.<glob>          top-level input ports
#   oport.<glob>          top-level output ports
#   seq.<glob>            VIRTUAL: sequential instances (flop/latch)
#   gate.<glob>           VIRTUAL: non-sequential instances
#
# Sugar:
#   inst.<typeglob>.<nameglob>   # e.g., inst.mioc_flop.u*
#     ⇒ same as: find -src inst.<nameglob> -type <typeglob>
#
# Flags:
#   -type <glob>   filter instance cell types (repeatable; matches ANY)
#   -cross_sync    allow traversal through sequential cells (default: stop at flops/latches)
#   -tree          render all found paths as a prefix tree
#   -max_nodes N   cap on visited nodes during DFS (default env FIND_MAX_NODES=20000)
#   -max_paths N   cap on number of paths collected (default env FIND_MAX_PATHS=2000)
#   -max_depth N   cap on path length (edge count)
#   -back          traverse in fanin direction (reverse)
#   -label_types   annotate inst nodes as inst.NAME[TYPE] (fallback [SEQ] if unknown but sequential)
#   -show_stops    if no full path reaches -dst, also print partial paths to stop points with STOP:<reason>
#
def _handler(rest: str, interp) -> str:
    (src, dst, cross, tree, type_globs, max_nodes, max_paths,
     max_depth, back, label_types, show_stops) = _parse_args(rest)

    # Build net driver/load index once
    idx = _index_net_sides(interp)

    # Simple listings
    if src and not dst:
        k, pat = _kind_and_glob(src)

        if k in ('inst','seq','gate'):
            names = list((interp.graph.instances or {}).keys())
            sugar_tpat, npat = _split_inst_type_sugar(pat) if k == 'inst' else (None, pat)
            name_filtered = _match_set(names, npat)
            if k == 'seq':
                name_filtered = [n for n in name_filtered if _cell_is_sequential(interp, n)]
            elif k == 'gate':
                name_filtered = [n for n in name_filtered if not _cell_is_sequential(interp, n)]
            eff_type_globs = list(type_globs)
            if sugar_tpat:
                eff_type_globs.append(sugar_tpat)
            name_filtered = [n for n in name_filtered if _type_matches(interp, n, eff_type_globs)]
            if label_types:
                # annotate instance list with [TYPE] (fallback [SEQ])
                out = []
                for n in sorted(set(name_filtered)):
                    ctype = _cell_type_of(interp, n)
                    if not ctype and _cell_is_sequential(interp, n):
                        ctype = "SEQ"
                    out.append(f"{n}[{ctype}]" if ctype else n)
                return "\n".join(out)
            return "\n".join(sorted(set(name_filtered)))

        elif k == 'net':
            names = list((interp.graph.nets or {}).keys())
            return "\n".join(_match_set(names, pat))

        elif k in ('iport','oport'):
            names = list((interp.graph.top_inputs or set()) or []) if k=='iport' \
                    else list((interp.graph.top_outputs or set()) or [])
            return "\n".join(_match_set(names, pat))

        return "usage: find -src <inst.*|net.*|iport.*|oport.*|seq.*|gate.*> [-type <glob>]... [-label_types]"

    # Path search mode
    if not (src and dst):
        return "usage: find -src <kind.pattern> -dst <kind.pattern> [-type <glob>]... [-cross_sync] [-tree] [-max_nodes N] [-max_paths N] [-max_depth N] [-back] [-label_types] [-show_stops]"

    skind, spat = _kind_and_glob(src)
    dkind, dpat = _kind_and_glob(dst)

    s_type_sugar, s_name_glob = (None, spat)
    d_type_sugar, d_name_glob = (None, dpat)
    if skind == 'inst':
        s_type_sugar, s_name_glob = _split_inst_type_sugar(spat)
    if dkind == 'inst':
        d_type_sugar, d_name_glob = _split_inst_type_sugar(dpat)

    eff_src_types = list(type_globs)
    eff_dst_types = list(type_globs)
    if s_type_sugar: eff_src_types.append(s_type_sugar)
    if d_type_sugar: eff_dst_types.append(d_type_sugar)

    # Build src node set
    if skind in ('inst','seq','gate'):
        all_insts = list((interp.graph.instances or {}).keys())
        name_glob = s_name_glob if skind=='inst' else spat
        s_candidates = _match_set(all_insts, name_glob)
        if skind == 'seq':
            s_candidates = [n for n in s_candidates if _cell_is_sequential(interp, n)]
        elif skind == 'gate':
            s_candidates = [n for n in s_candidates if not _cell_is_sequential(interp, n)]
        s_candidates = [n for n in s_candidates if _type_matches(interp, n, eff_src_types)]
        src_nodes = [('inst', n) for n in s_candidates]

    elif skind == 'net':
        s_candidates = _match_set((interp.graph.nets or {}).keys(), spat)
        src_nodes = [('net', n) for n in s_candidates]

    elif skind in ('iport','oport'):
        nets = (interp.graph.top_inputs or set()) if skind=='iport' else (interp.graph.top_outputs or set())
        s_candidates = _match_set(nets, spat)
        src_nodes = [('net', n) for n in s_candidates]

    else:
        return "Only inst.*|seq.*|gate.*|net.*|iport.*|oport.* supported for -src"

    # Destination predicate
    def _dst_pred(node: Tuple[str,str]) -> bool:
        t,v = node
        if dkind in ('inst','seq','gate') and t == 'inst':
            name_ok = fnmatch.fnmatch(v, d_name_glob if dkind=='inst' else dpat)
            if not name_ok:
                return False
            if dkind == 'seq' and not _cell_is_sequential(interp, v):
                return False
            if dkind == 'gate' and _cell_is_sequential(interp, v):
                return False
            if not _type_matches(interp, v, eff_dst_types):
                return False
            return True

        if dkind == 'net' and t == 'net':
            return fnmatch.fnmatch(v, dpat)

        if dkind == 'iport' and t == 'net':
            return v in (interp.graph.top_inputs or set())

        if dkind == 'oport' and t == 'net':
            return v in (interp.graph.top_outputs or set())

        return False

    # Traverse
    paths, truncated, stop_paths, stop_reasons = _dfs_all_paths(
        interp, _index_net_sides(interp),
        src_nodes, _dst_pred,
        allow_cross=cross, forward=(not back),
        max_nodes=max_nodes, max_paths=max_paths, max_depth=max_depth,
        collect_stops=show_stops
    )

    fmt_node = _make_fmt(interp, label_types=label_types)

    out_chunks: List[str] = []

    # Regular matches (full paths to dst)
    if paths:
        body = _render_tree(paths, fmt_node) if tree else _render_path(paths, fmt_node)
        out_chunks.append(body)

    # Stops (partial paths) if requested and useful
    if show_stops and stop_paths:
        if paths:
            out_chunks.append("")  # blank line separator
        # Render stops as straight paths with a marker on the final node
        out_chunks.append(_render_path(stop_paths, fmt_node, stop_reasons))

    body = "\n".join(out_chunks).strip()

    if truncated:
        tail = "\n[find: output truncated — raise -max_nodes/-max_paths/-max_depth to explore more]"
        body = (body + tail) if body else tail.strip()

    return body

def register(reg: CommandRegistry):
    reg.register(
        "find",
        _handler,
        "Unified list/path/fanin/fanout; -src/-dst/-type/-cross_sync/-tree (-max_nodes/-max_paths/-max_depth, -back for fanin, -label_types for inst.NAME[TYPE], -show_stops to mark partial paths)"
    )
