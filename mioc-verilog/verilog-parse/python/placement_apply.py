# 2025-10-07  r1  by:ediaz  tag:gui
# placement_apply.py — Tiny Core
#
# Purpose
#   Apply a file-driven placement to the current in-memory graph.
#   Reads data-in/placement.csv with headers: id,col,row (or ID,col,row),
#   converts (col,row) to pixel {x,y} on a grid, and writes into node
#   positions for common graph shapes (dict of nodes, iterable, etc.).
#
# Public API
#   apply_from_csv(interpreter, csv_path=Path("data-in/placement.csv"),
#                  grid_w=180, grid_h=110, margin_x=40, margin_y=40) -> dict
#     - Returns a report: {"applied": int, "missing": [ids], "extra": [ids]}
#
# Notes
#   - This does NOT validate exact ID equality; use cmd_gui.py for gating.
#   - Safe to call before/after export; it mutates in-memory positions only.
#   - Tries multiple graph shapes to avoid tight coupling.
# -------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Any, List, Set, Optional
import csv

# ---------------------- CSV parsing -------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    col: int
    row: int

def _read_csv(csv_path: Path) -> Dict[str, Place]:
    rows: Dict[str, Place] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        try:
            header = next(rdr)
        except StopIteration:
            return rows
        header = [h.strip() for h in header]
        # header keys
        id_idx = header.index("id") if "id" in header else (header.index("ID") if "ID" in header else -1)
        try:
            col_idx = next(i for i,h in enumerate(header) if h.lower()=="col")
            row_idx = next(i for i,h in enumerate(header) if h.lower()=="row")
        except StopIteration:
            col_idx = row_idx = -1
        if id_idx < 0 or col_idx < 0 or row_idx < 0:
            raise ValueError(f"[placement_apply] Bad CSV header, expected id,col,row or ID,col,row; got {header}")

        for line in rdr:
            if not line: 
                continue
            # pad/truncate defensively
            parts = [p.strip() for p in line]
            if max(id_idx, col_idx, row_idx) >= len(parts):
                continue
            sid = parts[id_idx]
            if not sid:
                continue
            try:
                col = int(parts[col_idx])
                row = int(parts[row_idx])
            except Exception:
                continue
            rows[str(sid)] = Place(id=str(sid), col=col, row=row)
    return rows

# ---------------------- Graph helpers -----------------------------------

def _colrow_to_xy(col:int, row:int, grid_w:int, grid_h:int, margin_x:int, margin_y:int) -> Tuple[int,int]:
    return (margin_x + col * grid_w, margin_y + row * grid_h)

def _iter_nodes(graph: Any) -> Iterable[Any]:
    """
    Yield node-like objects for common shapes:
      - graph.nodes: dict-like -> values
      - graph.nodes: iterable -> items
      - graph.get_nodes(): iterable
    Each yielded item should expose id via .id or ['id'].
    """
    if graph is None:
        return []
    # dict-like
    nodes = getattr(graph, "nodes", None)
    if isinstance(nodes, dict):
        return nodes.values()
    # iterable
    if nodes is not None and hasattr(nodes, "__iter__"):
        return nodes
    # accessor
    if hasattr(graph, "get_nodes"):
        try:
            return graph.get_nodes()
        except Exception:
            pass
    # fallback: empty
    return []

def _get_node_id(n: Any) -> Optional[str]:
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
            if isinstance(nid, (str,int)):
                return str(nid)
        except Exception:
            pass
    return None

def _set_node_xy(n: Any, x: int, y: int) -> bool:
    """
    Try several ways to set a node's position. Return True if we succeeded.
    """
    # Common libs: setPosition / position
    for meth in ("setPosition", "set_position", "position", "setXY", "moveTo", "move_to"):
        fn = getattr(n, meth, None)
        if callable(fn):
            try:
                # Try various signatures
                try:
                    fn(x, y); return True
                except TypeError:
                    pass
                try:
                    fn({"x": x, "y": y}); return True
                except TypeError:
                    pass
                try:
                    fn(x=x, y=y); return True
                except TypeError:
                    pass
            except Exception:
                pass

    # Common attributes
    try:
        setattr(n, "x", x)
        setattr(n, "y", y)
        return True
    except Exception:
        pass

    # Mapping
    try:
        n["x"] = x  # type: ignore[index]
        n["y"] = y  # type: ignore[index]
        return True
    except Exception:
        pass

    return False

def _post_apply_refresh(graph: Any) -> None:
    for meth in ("refresh", "fit", "resize", "relayout", "redraw"):
        fn = getattr(graph, meth, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass

# ---------------------- Public entrypoint --------------------------------

def apply_from_csv(interpreter: Any,
                   csv_path: Path = Path("data-in/placement.csv"),
                   grid_w: int = 180, grid_h: int = 110,
                   margin_x: int = 40, margin_y: int = 40) -> Dict[str, Any]:
    """
    Apply placement to the graph inside 'interpreter' using CSV file.
    Returns a report dict: {"applied": int, "missing": [ids], "extra": [ids]}.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"[placement_apply] placement CSV not found: {csv_path}")

    placements = _read_csv(csv_path)
    # grab a graph from typical attribute names
    graph = None
    for attr in ("graph", "netgraph", "design", "model"):
        g = getattr(interpreter, attr, None)
        if g is not None:
            graph = g
            break
    if graph is None:
        raise RuntimeError("[placement_apply] Could not find a graph on the interpreter.")

    applied = 0
    seen_ids: Set[str] = set()
    for n in _iter_nodes(graph):
        nid = _get_node_id(n)
        if nid is None:
            continue
        seen_ids.add(nid)
        p = placements.get(nid)
        if not p:
            continue
        x, y = _colrow_to_xy(p.col, p.row, grid_w, grid_h, margin_x, margin_y)
        if _set_node_xy(n, x, y):
            applied += 1

    _post_apply_refresh(graph)

    csv_ids = set(placements.keys())
    missing = sorted(seen_ids - csv_ids)
    extra   = sorted(csv_ids - seen_ids)

    return {"applied": applied, "missing": missing, "extra": extra}


# ---------------------- CLI helper (optional) ----------------------------

def _main(argv: Optional[Iterable[str]] = None) -> int:
    """
    Minimal CLI for ad-hoc testing:
      python -m placement_apply  [--csv path] [--grid-w N] [--grid-h N]
                                 [--margin-x N] [--margin-y N]
    Note: requires a running interpreter with a loaded graph and a shim
    exposing it as placement_apply._TEST_INTERPRETER (for dev only).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Apply placement to in-memory graph")
    parser.add_argument("--csv", default="data-in/placement.csv")
    parser.add_argument("--grid-w", type=int, default=180)
    parser.add_argument("--grid-h", type=int, default=110)
    parser.add_argument("--margin-x", type=int, default=40)
    parser.add_argument("--margin-y", type=int, default=40)
    args = parser.parse_args(list(argv) if argv is not None else None)

    interp = globals().get("_TEST_INTERPRETER")
    if interp is None:
        print("[placement_apply] No _TEST_INTERPRETER bound; this CLI is for dev testing only.")
        return 2

    rep = apply_from_csv(interp,
                         csv_path=Path(args.csv),
                         grid_w=args.grid_w, grid_h=args.grid_h,
                         margin_x=args.margin_x, margin_y=args.margin_y)
    print(rep)
    return 0

if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_main(_sys.argv[1:]))
