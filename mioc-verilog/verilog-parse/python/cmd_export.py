# === VNLT REV ===
# file: python/cmd_export.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List, Optional, Any, Tuple
import json
import os
import registry as _reg  # for REG and CommandRegistry

SUMMARY = "export json [--to FILE] — write current design to a JSON file for the HTML GUI"
DETAIL = """
export json [--to FILE]

Write the current netlist/graph to a JSON file in a GUI-agnostic schema.

Nodes:
  - Instances:  { id, label=<cell type>, type=('seq'|'comb'), ports:[{name}, ...], attrs:{...} }
  - IO signals: { id, label, type='io' }

Edges:
  - Instance→Instance (one per driver→load pin pair, per net)
  - **Top Input → Instance** (one per load pin of that input net)
  - **Instance → Top Output** (one per driver pin of that output net)

Also includes:
  io: { inputs:[...], outputs:[...] }
  _meta: { node_count, edge_count }

Examples:
  export json
  export json --to build/graph.json
""".strip()


def _parse_args(argv: List[str]):
    fmt = None
    out = "graph.json"
    tokens = list(argv or [])
    if tokens and tokens[0].lower() == "json":
        fmt = tokens.pop(0).lower()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "--to" and i + 1 < len(tokens):
            out = tokens[i + 1]
            i += 2
        else:
            i += 1
    return {"fmt": fmt, "to": out}


def _is_seq(cell_type: str) -> bool:
    tl = (cell_type or "").lower()
    return any(k in tl for k in ("dff", "flop", "latch", "ff", "seq"))


def _get_graph(interp: Any):
    return getattr(interp, "graph", None)


def run(argv: List[str], interp) -> Optional[dict]:
    args = _parse_args(argv)
    if args.get("fmt") != "json":
        print("ERROR: Only 'export json' is supported at this time.")
        return None

    G = _get_graph(interp)
    if G is None:
        print("ERROR: No netlist/graph is loaded. Use 'read verilog <manifest>' first.")
        return None

    out_path = args.get("to") or "graph.json"
    if os.path.dirname(out_path):
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        except Exception:
            pass

    payload = {
        "top": getattr(G, "top", "") or "(unknown)",
        "version": "v0.6.6",
        "tool": {"name": "VNLT", "version": "v0.6.6"},
        "nodes": [],
        "edges": [],
        "io": {
            "inputs": list(getattr(G, "top_inputs", []) or []),
            "outputs": list(getattr(G, "top_outputs", []) or []),
        },
        "_meta": {},
    }

    # ---------- Nodes ----------
    # Instances as components (including iobuf / iobuf_n)
    for iname, inst in (G.instances or {}).items():
        cell = inst.get("type", "") or inst.get("cell_type", "")
        ports = [{"name": p} for p in sorted((inst.get("pins") or {}).keys())]
        ntype = "seq" if _is_seq(cell) else "comb"
        payload["nodes"].append({
            "id": iname,
            "label": cell or iname,
            "type": ntype,
            "ports": ports,
            "attrs": dict(inst),
        })

    # Top-level IO nodes (ports)
    for net in payload["io"]["inputs"]:
        payload["nodes"].append({"id": net, "label": net, "type": "io", "ports": []})
    for net in payload["io"]["outputs"]:
        payload["nodes"].append({"id": net, "label": net, "type": "io", "ports": []})

    # ---------- Edges ----------
    # We build three kinds of edges:
    #   1) Instance→Instance from net drivers to loads (normal internal wiring)
    #   2) TopInput→Instance for input nets (so left-side IO tiles are visually connected)
    #   3) Instance→TopOutput for output nets (so right-side IO tiles are visually connected)
    edges: List[dict] = []
    seen: set[Tuple[str, str, str, str, str]] = set()  # (src,dst,src_port,dst_port,net)

    def add_edge(src: str, dst: str, net: str, src_port: str = "", dst_port: str = ""):
        key = (str(src), str(dst), str(src_port or ""), str(dst_port or ""), str(net or ""))
        if key in seen:
            return
        seen.add(key)
        edges.append({
            "src": str(src),
            "dst": str(dst),
            "src_port": str(src_port or ""),
            "dst_port": str(dst_port or ""),
            "net": str(net or ""),
        })

    top_inputs = set(payload["io"]["inputs"])
    top_outputs = set(payload["io"]["outputs"])

    # Iterate nets and stitch all three edge classes
    for nname, nd in (G.nets or {}).items():
        drivers = list(nd.get("drivers", []) or [])   # [(inst, pin), ...]
        loads   = list(nd.get("loads", []) or [])     # [(inst, pin), ...]

        # (1) Instance→Instance edges
        for dinst, dport in drivers:
            for linst, lport in loads:
                if dinst and linst:
                    add_edge(dinst, linst, nname, dport or "", lport or "")

        # (2) Top Input → Instance edges
        if nname in top_inputs:
            for linst, lport in loads:
                if linst:
                    add_edge(nname, linst, nname, "", lport or "")

        # (3) Instance → Top Output edges
        if nname in top_outputs:
            for dinst, dport in drivers:
                if dinst:
                    add_edge(dinst, nname, nname, dport or "", "")

    payload["edges"] = edges

    # ---------- Meta ----------
    payload["_meta"]["node_count"] = len(payload["nodes"])
    payload["_meta"]["edge_count"] = len(payload["edges"])

    # ---------- Write ----------
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Wrote JSON export to: {out_path}")
        print(f"  nodes={payload['_meta']['node_count']} edges={payload['_meta']['edge_count']}")
    except Exception as e:
        print(f"ERROR: Failed to export JSON: {e}")

    return None


def help() -> str:
    return DETAIL


def register(reg: _reg.CommandRegistry):
    reg.add_command("export", run, SUMMARY, DETAIL, aliases=None)
