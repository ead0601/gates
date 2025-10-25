# === VNLT REV ===
# file: cmds/cmd_read_verilog.py
# rev:  2025-10-20 13:27  r6a by:Drater  tag:cmd
# note: Manifest-aware; calls builders.build_celllib(rtl, seq_cells) and build_netgraph(celllib, components, assigns, top);
#       converts to gates.CellLib/Graph and loads via Interpreter.attach(...).
#       r6a+dbg — guarded diagnostics with vnlt_utils.dbg (prefix 'read_verilog').
# === /VNLT REV ===

import os
import re
from typing import List, Dict, Tuple, Optional
from registry import CommandRegistry
from gates import CellLib, Graph
from vnlt_utils import dbg

_VERI_EXT = (".v", ".sv", ".vh", ".svh")

def _looks_verilog(path: str) -> bool:
    s = path.strip().strip('\"\'')
    return s.lower().endswith(_VERI_EXT)

def _as_abs(base: str, p: str) -> str:
    p = p.strip().strip('\"\'')
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else os.path.abspath(os.path.join(base, p))

def _split_seq_list(s: str) -> List[str]:
    # Accept comma or whitespace separated
    toks = [t for t in re.split(r'[\s,]+', s.strip()) if t]
    return toks

def _read_manifest(path: str) -> Tuple[Dict[str, List[str]], Optional[str], List[str]]:
    base = os.path.abspath(os.path.dirname(path))
    rtl: List[str] = []
    comps: List[str] = []
    assigns: List[str] = []
    seq_cells: List[str] = []
    top: Optional[str] = None
    seen = set()

    with open(path, "r", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if ":" in s:
                k, v = s.split(":", 1)
                k = k.strip().lower(); v = v.strip()
                if k in ("top","top_module","topmod"):
                    v = v.strip('\"\'')
                    if v:
                        top = v
                    continue
                if k in ("seq_cells","sequential","seq"):
                    seq_cells += _split_seq_list(v)
                    continue
                bucket = None
                if k in ("rtl","files","sources","source"): bucket = "rtl"
                elif k in ("components","comp","cells","celllib"): bucket = "components"
                elif k in ("assigns","assign","defs","define"): bucket = "assigns"
                if bucket:
                    if _looks_verilog(v):
                        ap = _as_abs(base, v)
                        if ap not in seen:
                            seen.add(ap)
                            (rtl if bucket=="rtl" else comps if bucket=="components" else assigns).append(ap)
                    continue
                # Unknown key — if value looks like file, default to components
                if _looks_verilog(v):
                    ap = _as_abs(base, v)
                    if ap not in seen:
                        seen.add(ap); comps.append(ap)
                continue
            # Bare token: treat as components (structural) if verilog-ish
            if _looks_verilog(s):
                ap = _as_abs(base, s)
                if ap not in seen:
                    seen.add(ap); comps.append(ap)
                continue

    # Deduplicate sequence cells preserving order
    seen_seq=set(); seq_cells=[c for c in seq_cells if not (c in seen_seq or seen_seq.add(c))]
    buckets = {"rtl": rtl, "components": comps, "assigns": assigns}
    return buckets, top, seq_cells

def _dict_to_celllib(celllib_dict: Dict) -> CellLib:
    cl = CellLib(cells = dict(celllib_dict.get("cells", {})))
    cl.finalize()
    return cl

def _dict_to_graph(graph_dict: Dict) -> Graph:
    top = graph_dict.get("top", {})
    top_inputs = set(top.get("inputs", []))
    top_outputs = set(top.get("outputs", []))
    nets = dict(graph_dict.get("nets", {}))

    # instances from list -> dict keyed by 'name' if necessary
    insts_raw = graph_dict.get("instances", [])
    if isinstance(insts_raw, dict):
        instances = dict(insts_raw)
    else:
        instances = { }
        for it in insts_raw:
            name = it.get("name")
            if name:
                instances[name] = {k:v for k,v in it.items() if k != "name"}

    aliases = dict(graph_dict.get("aliases", {}))
    return Graph(top_inputs=top_inputs, top_outputs=top_outputs, nets=nets, instances=instances, aliases=aliases)

def _handler(rest: str, interp) -> str:
    dbg(interp, "read_verilog", "start handler")
    arg = (rest or "").strip()
    dbg(interp, "read_verilog", "arg=%s", arg)
    if not arg:
        return "usage: read_verilog <manifest.txt>"
    if not os.path.exists(arg):
        return f"[read_verilog] manifest not found: {arg}"
    dbg(interp, "read_verilog", "manifest found: %s", arg)

    buckets, top, seq_cells = _read_manifest(arg)
    rtl = buckets["rtl"]; components = buckets["components"]; assigns = buckets["assigns"]
    dbg(interp, "read_verilog", "buckets: rtl=%d components=%d assigns=%d", len(rtl), len(components), len(assigns))
    dbg(interp, "read_verilog", "top=%s seq_cells=%d", top or '-', len(seq_cells or []))
    if not (rtl or components):
        dbg(interp, "read_verilog", "no verilog files in manifest")
        return "[read_verilog] no verilog files found in manifest"

    # Default seq_cells: use 'top' entry if present and looks sequential. Otherwise empty.
    if not seq_cells:
        seq_cells = []

    try:
        from builders import build_celllib, build_netgraph
    except Exception as e:
        return f"[read_verilog] import error (builders): {e}"

    dbg(interp, "read_verilog", "build_celllib(rtl=%d, seq_cells=%d)", len(rtl), len(seq_cells or []))
    try:
        celllib_dict = build_celllib(rtl, seq_cells)
        dbg(interp, "read_verilog", "celllib built: keys=%s", list(celllib_dict.keys())[:6])
        graph_dict   = build_netgraph(celllib_dict, components, assigns, top or "")
        # lightweight structure sizes
        di = graph_dict.get("instances", {})
        dn = graph_dict.get("nets", {})
        dbg(interp, "read_verilog", "graph built: instances=%s nets=%s", 
            (len(di) if hasattr(di,'__len__') else 'dict?'),
            (len(dn) if hasattr(dn,'__len__') else 'dict?'))
    except Exception as e:
        return f"[read_verilog] build failed: {e}"

    try:
        cl = _dict_to_celllib(celllib_dict)
        gr = _dict_to_graph(graph_dict)
        #interp.attach(cl, gr)
        interp.attach(graph=gr, celllib=cl)
        dbg(interp, "read_verilog", "attached: instances=%d nets=%d",
            len(getattr(gr, 'instances', {}) or {}),
            len(getattr(gr, 'nets', {}) or {}))
    except Exception as e:
        return f"[read_verilog] failed to load into interpreter: {e}"

    inst_n = len(getattr(interp.graph, "instances", {}) or {})
    nets_n = len(getattr(interp.graph, "nets", {}) or {})
    return f"Loaded: {len(rtl)+len(components)+len(assigns)} files; instances={inst_n} nets={nets_n} top={top or '-'}"

def register(reg: CommandRegistry):
    reg.register("read_verilog", _handler, "read_verilog <manifest> — parse/build/load design")
