# === VNLT REV ===
# file: python/placement_gen.py
# rev:  2025-10-07  r1  by: ediaz  tag: gui
# name: Tiny Core
#
# Purpose
#   Deterministic file-driven placement:
#     - Right→left layering with outputs on the rightmost column
#     - Outputs sorted A→Z
#     - Predecessors in each layer ordered by barycenter (relative to the layer to the right)
#   Writes CSV: data-in/placement.csv with header: id,col,row
#
# Public entrypoints (any of these may be called by cmd_gui):
#   generate(interpreter=None, out_path=Path('data-in/placement.csv'))
#   write_csv(*args, **kwargs)      # alias to generate
#   build_and_write(*args, **kwargs)# alias to generate
#   run(interpreter=None, out_path=...)  # alias to generate
#   main()                          # CLI for ad-hoc testing
# ----------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
import csv
import json
import collections

# ----------------------- Graph extraction --------------------------------

def _get_graph(interpreter: Any) -> Any:
    for attr in ("graph", "netgraph", "design", "model"):
        g = getattr(interpreter, attr, None)
        if g is not None:
            return g
    return None

def _node_id(n: Any) -> Optional[str]:
    # attribute
    nid = getattr(n, "id", None)
    if isinstance(nid, (str, int)):
        return str(nid)
    # mapping
    try:
        nid = n["id"]  # type: ignore[index]
        if isinstance(nid, (str, int)):
            return str(nid)
    except Exception:
        pass
    # method
    if hasattr(n, "get"):
        try:
            nid = n.get("id")  # type: ignore[attr-defined]
            if isinstance(nid, (str, int)):
                return str(nid)
        except Exception:
            pass
    return None

def _iter_nodes(g: Any) -> Iterable[Any]:
    if g is None:
        return []
    nodes = getattr(g, "nodes", None)
    if isinstance(nodes, dict):
        return nodes.values()
    if nodes is not None and hasattr(nodes, "__iter__"):
        return nodes
    if hasattr(g, "get_nodes"):
        try:
            return g.get_nodes()
        except Exception:
            pass
    return []

def _extract_nodes(g: Any) -> List[str]:
    ids: List[str] = []
    seen: Set[str] = set()
    for n in _iter_nodes(g):
        nid = _node_id(n)
        if nid is None or nid in seen:
            continue
        seen.add(nid)
        ids.append(nid)
    return ids

def _norm_edge(e: Any) -> Optional[Tuple[str, str]]:
    # tuple/list style
    if isinstance(e, (tuple, list)) and len(e) >= 2:
        a, b = e[0], e[1]
        if isinstance(a, (str, int)) and isinstance(b, (str, int)):
            return (str(a), str(b))
        # object with .id
        a_id = getattr(a, "id", None)
        b_id = getattr(b, "id", None)
        if a_id is not None and b_id is not None:
            return (str(a_id), str(b_id))
    # dict style
    if isinstance(e, dict):
        for ksrc, kdst in (("source","target"), ("src","dst"), ("u","v"), ("from","to")):
            if ksrc in e and kdst in e:
                a, b = e[ksrc], e[kdst]
                if a is not None and b is not None:
                    return (str(getattr(a,"id",a)), str(getattr(b,"id",b)))
    # object style
    for ksrc, kdst in (("source","target"), ("src","dst"), ("u","v")):
        if hasattr(e, ksrc) and hasattr(e, kdst):
            a = getattr(e, ksrc)
            b = getattr(e, kdst)
            return (str(getattr(a,"id",a)), str(getattr(b,"id",b)))
    return None

def _iter_edges(g: Any) -> Iterable[Any]:
    if g is None:
        return []
    edges = getattr(g, "edges", None)
    if edges is not None and hasattr(edges, "__iter__"):
        return edges
    if hasattr(g, "get_edges"):
        try:
            return g.get_edges()
        except Exception:
            pass
    # Try per-node fanout
    for n in _iter_nodes(g):
        outs = None
        for attr in ("successors", "succ", "fanout", "outs", "neighbors_out"):
            if hasattr(n, attr):
                try:
                    outs = getattr(n, attr)()
                except TypeError:
                    outs = getattr(n, attr)
                break
        if outs is None:
            continue
        src = _node_id(n)
        if src is None:
            continue
        for o in outs or []:
            tid = _node_id(o)
            if tid is None:
                continue
            yield (src, tid)
    return []

def _extract_edges(g: Any) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for e in _iter_edges(g):
        uv = _norm_edge(e)
        if uv is None and isinstance(e, tuple) and len(e) == 2 and all(isinstance(x,str) for x in e):
            uv = (e[0], e[1])
        if uv is None:
            continue
        out.append(uv)
    return out

# ----------------------- Layering & ordering -----------------------------

def _build_adj(nodes: List[str], edges: List[Tuple[str,str]]):
    succ = {u: [] for u in nodes}
    pred = {u: [] for u in nodes}
    for u, v in edges:
        if u in succ and v in succ:
            succ[u].append(v)
            pred[v].append(u)
    return succ, pred

def _outputs(nodes: List[str], succ: Dict[str, List[str]]) -> List[str]:
    return [n for n in nodes if len(succ.get(n, [])) == 0]

def _distance_to_output(nodes: List[str], pred: Dict[str, List[str]], outs: List[str]) -> Dict[str, int]:
    # BFS from all outputs going backwards via predecessors
    from collections import deque
    dist = {n: 10**9 for n in nodes}
    dq = deque()
    for o in outs:
        dist[o] = 0
        dq.append(o)
    while dq:
        x = dq.popleft()
        for p in pred.get(x, []):
            if dist[p] > dist[x] + 1:
                dist[p] = dist[x] + 1
                dq.append(p)
    # for isolated or cycles unreachable, clamp to max
    maxd = max((d for d in dist.values() if d < 10**9), default=0)
    for n in nodes:
        if dist[n] >= 10**9:
            dist[n] = maxd + 1
    return dist

def _barycenter_order(col_nodes: List[str], succ: Dict[str, List[str]], right_order: Dict[str, int]) -> List[str]:
    # barycenter based on positions in layer to the right
    def bary(n: str) -> float:
        nbrs = [right_order[v] for v in succ.get(n, []) if v in right_order]
        if not nbrs:
            return float('inf')
        return sum(nbrs) / len(nbrs)
    return sorted(col_nodes, key=lambda n: (bary(n), n))

def _compute_layers(nodes: List[str], edges: List[Tuple[str,str]]) -> Dict[str, Tuple[int,int]]:
    # Build adjacency
    succ, pred = _build_adj(nodes, edges)
    outs = _outputs(nodes, succ)
    # Determine columns: outputs should be on rightmost (highest col)
    dist = _distance_to_output(nodes, pred, outs)
    maxd = max(dist.values()) if dist else 0
    col = {n: maxd - dist[n] for n in nodes}  # outputs get maxd
    # Group nodes by column
    cols: Dict[int, List[str]] = collections.defaultdict(list)
    for n in nodes:
        cols[col[n]].append(n)
    # Rightmost column ordering (outputs): A→Z
    max_col = max(cols.keys()) if cols else 0
    cols[max_col] = sorted(cols[max_col])
    # Proceed right→left, order by barycenter relative to right neighbor positions
    order_in_col: Dict[int, Dict[str,int]] = {}
    order_in_col[max_col] = {nid: i for i, nid in enumerate(cols[max_col])}
    for c in range(max_col - 1, -1, -1):
        right_order = order_in_col.get(c + 1, {})
        ordered = _barycenter_order(cols.get(c, []), succ, right_order)
        cols[c] = ordered
        order_in_col[c] = {nid: i for i, nid in enumerate(ordered)}
    # Produce (col,row) mapping
    pos: Dict[str, Tuple[int,int]] = {}
    for c, arr in cols.items():
        for r, nid in enumerate(arr):
            pos[nid] = (c, r)
    return pos

# ----------------------- CSV writer -------------------------------------

def _write_csv(path: Path, positions: Dict[str, Tuple[int,int]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort rows by col asc then row asc for stable output
    rows = [(nid, c, r) for nid, (c, r) in positions.items()]
    rows.sort(key=lambda t: (t[1], t[2], t[0]))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "col", "row"])
        for nid, c, r in rows:
            w.writerow([nid, c, r])
    return path

# ----------------------- Public API -------------------------------------

def generate(interpreter: Any = None, out_path: Path | str = Path("data-in/placement.csv")) -> Path:
    """
    Compute deterministic placement and write CSV.
    Accepts out_path as Path or str. Returns the written Path.
    """
    if isinstance(out_path, str):
        out_path = Path(out_path)
    if interpreter is None:
        raise RuntimeError("placement_gen.generate requires an interpreter with a loaded graph")
    g = _get_graph(interpreter)
    nodes = _extract_nodes(g)
    # If no nodes found, try to recover from volatile/graph.json to stay useful
    if not nodes:
        gj = Path(__file__).resolve().parent.parent / "volatile" / "graph.json"
        if gj.exists():
            try:
                data = json.loads(gj.read_text(encoding="utf-8"))
                nodes = [str(n.get("id")) for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n]
                edges = [(str(e.get("source")), str(e.get("target"))) for e in data.get("edges", []) if isinstance(e, dict) and "source" in e and "target" in e]
            except Exception:
                nodes = []
                edges = []
        if not nodes:
            raise RuntimeError("placement_gen: unable to enumerate nodes from interpreter or graph.json")
    else:
        edges = _extract_edges(g)

    positions = _compute_layers(nodes, edges)
    return _write_csv(Path(out_path), positions)

# Aliases
def write_csv(*args, **kwargs): return generate(*args, **kwargs)
def build_and_write(*args, **kwargs): return generate(*args, **kwargs)
def run(*args, **kwargs): return generate(*args, **kwargs)

# ----------------------- CLI (optional) ----------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Dev-only CLI (expects interpreter injected if used programmatically).
    """
    import argparse
    p = argparse.ArgumentParser(description="Generate deterministic placement CSV")
    p.add_argument("--out", default="data-in/placement.csv")
    args = p.parse_args(list(argv) if argv is not None else None)
    try:
        generate(interpreter=None, out_path=Path(args.out))  # will raise without interpreter
    except Exception as e:
        print(f"[placement_gen] ERROR: {e}")
        return 2
    return 0

if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main(_sys.argv[1:]))
