#!/usr/bin/env python3
"""
Step 2 (Option A): Build connectivity graph and emit aliases for PIN_IN_* taps.

What’s new:
- Detect assigns of the form:   assign PIN_IN_<N> =  <ID>;   -> BUF (buf1)
                                assign PIN_IN_<N> = ~<ID>;   -> INV (inv1)
- Create synthetic instances:
    assign_PIN_IN_12: inv1 (in1=BA6, z=PIN_IN_12)
    assign_PIN_IN_13: buf1 (in1=BA7, z=PIN_IN_13)
- Tag the **RHS identifiers** (e.g., BA6, BA7) as top inputs (top_in).
- Emit an "aliases" map in netgraph.json:
    "aliases": {
      "PIN_IN_12": {"display":"BA6","invert":true,"kind":"top_in"},
      "PIN_IN_13": {"display":"BA7","invert":false,"kind":"top_in"}
    }
- Do NOT tag PIN_IN_* as top_in by name anymore.

Top outputs (e.g., assign RA7 = w_foo;) remain as synthetic BUF/INV to PORT and are tagged as top_out.

Usage:
  python3 step2_build_graph.py \
    --celllib ./celllib.json \
    --components /mnt/data/mioc_components.v \
    --assigns /mnt/data/mioc_pin_assignments.v \
    --out ./netgraph.json

python3 step2_build_graph.py   --celllib ./celllib.json   --components ./mioc_components.v   --assigns ./mioc_pin_assignments.v   --out ./netgraph.json


"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# ----- Regex helpers -----

RE_MODULE_INST = re.compile(r'^\s*([A-Za-z_]\w*)\s+(\w+)\s*\((.*?)\)\s*;', re.S | re.M)
RE_NAMED_CONN  = re.compile(r'\.(\w+)\s*\(\s*([^)]+?)\s*\)')
RE_ASSIGN      = re.compile(r'assign\s+([A-Za-z_]\w*)\s*=\s*([A-Za-z0-9_\'\[\]\(\)\s:~]+?)\s*;', re.M)
RE_WIRE_SIMPLE = re.compile(r'^\s*wire\s+(?:\[[^\]]+\]\s*)?(\w+)\s*;', re.M)
RE_LINE_COMMENT = re.compile(r'//.*')

RE_RHS_INV   = re.compile(r'^\s*~\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$')
RE_RHS_ID    = re.compile(r'^\s*([A-Za-z_]\w*)\s*$')
RE_RHS_CONST = re.compile(r"^\s*1'b([01])\s*$")

CONST_NETS = {"1'b0", "1'b1"}

def strip_line_comments(text: str) -> str:
    return RE_LINE_COMMENT.sub('', text)

# ----- Data structures -----

class CellLib:
    def __init__(self, data: dict):
        self.cells = data.get("cells", {})
        self.pin_dir: Dict[str, Dict[str, str]] = {}
        self.category: Dict[str, str] = {}
        for ctype, meta in self.cells.items():
            inputs = set(meta.get("inputs", []))
            outputs = set(meta.get("outputs", []))
            pd = {}
            for p in inputs:
                pd[p] = "in"
            for p in outputs:
                if p in pd:
                    raise ValueError(f"[celllib] Pin appears as both input and output in {ctype}: {p}")
                pd[p] = "out"
            self.pin_dir[ctype] = pd
            self.category[ctype] = meta.get("category", "comb")

    def has_cell(self, ctype: str) -> bool:
        return ctype in self.cells

class GraphBuilder:
    def __init__(self, celllib: CellLib):
        self.celllib = celllib
        self.instances: List[dict] = []     # list of {name,type,pins}
        self.nets: Dict[str, dict] = {}     # net -> {drivers:[], loads:[], tags:[]}
        self.top_inputs: Set[str] = set()
        self.top_outputs: Set[str] = set()
        self.constants: Set[str] = set()
        self.aliases: Dict[str, dict] = {}  # e.g., "PIN_IN_12": {"display":"BA6","invert":True,"kind":"top_in"}

    def _net(self, name: str) -> dict:
        if name not in self.nets:
            self.nets[name] = {"drivers": [], "loads": [], "tags": []}
        return self.nets[name]

    def tag_top_in(self, net: str):
        self.top_inputs.add(net)
        n = self._net(net)
        if "top_in" not in n["tags"]:
            n["tags"].append("top_in")

    def tag_top_out(self, net: str):
        self.top_outputs.add(net)
        n = self._net(net)
        if "top_out" not in n["tags"]:
            n["tags"].append("top_out")

    def add_instance(self, name: str, ctype: str, pins: Dict[str, str], synthetic: bool=False):
        # Validation for non-synthetic instances
        if not synthetic and not self.celllib.has_cell(ctype):
            raise ValueError(f"[E] Unknown cell type '{ctype}' for instance {name}")
        if not synthetic:
            known = self.celllib.pin_dir.get(ctype, {})
            for pin in pins.keys():
                if pin not in known:
                    raise ValueError(f"[E] Unknown pin '{pin}' on type '{ctype}' for instance {name}")

        self.instances.append({"name": name, "type": ctype, "pins": dict(pins)})

        # Direction map
        if synthetic and ctype in ("buf1", "inv1"):
            pin_dir_map = {"in1": "in", "z": "out"}
        else:
            pin_dir_map = self.celllib.pin_dir.get(ctype, {})

        for pin, net in pins.items():
            if net in CONST_NETS:
                self.constants.add(net)
            entry = self._net(net)
            role = pin_dir_map.get(pin)
            if role == "out":
                entry["drivers"].append([name, pin])
            elif role == "in":
                entry["loads"].append([name, pin])
            else:
                entry["loads"].append([name, pin])

    # --- Assign handling ---

    @staticmethod
    def _analyze_rhs(rhs: str) -> Tuple[str, Optional[str], bool]:
        """
        Analyze RHS text and return (kind, id_or_const, invert_flag)
        kind: "id" | "const" | "other"
        If kind == "id", id_or_const is the identifier name.
        If kind == "const", id_or_const is "1'b0" or "1'b1".
        invert_flag reflects '~' usage only when kind == "id" or "const".
        """
        s = rhs.strip()
        m = RE_RHS_INV.match(s)
        if m:
            ident = m.group(1)
            return ("id", ident, True)
        m = RE_RHS_CONST.match(s)
        if m:
            bit = m.group(1)
            return ("const", f"1'b{bit}", False)
        m = RE_RHS_ID.match(s)
        if m:
            ident = m.group(1)
            return ("id", ident, False)
        return ("other", s, False)

    def add_assign_pin_in(self, pin_in_net: str, rhs: str):
        """
        PIN_IN_* tap: create synthetic BUF/INV from the *RHS identifier* to PIN_IN_*,
        tag the RHS identifier as top input, and record an alias.
        """
        kind, data, inv = self._analyze_rhs(rhs)
        # Default pins
        if kind == "id":
            src = data
            ctype = "inv1" if inv else "buf1"
            self._net(pin_in_net)
            self._net(src)
            # Tag the real external port as top input
            self.tag_top_in(src)
            # Synthetic instance
            self.add_instance(f"assign_{pin_in_net}", ctype, {"in1": src, "z": pin_in_net}, synthetic=True)
            # Alias for renderer
            self.aliases[pin_in_net] = {"display": src, "invert": bool(inv), "kind": "top_in"}
        elif kind == "const":
            # Treat constants as source; still synthesize a buf
            src = data
            self._net(pin_in_net)
            self._net(src)
            self.add_instance(f"assign_{pin_in_net}", "buf1", {"in1": src, "z": pin_in_net}, synthetic=True)
            # Alias: display constant as-is
            self.aliases[pin_in_net] = {"display": src, "invert": False, "kind": "const"}
        else:
            # Fallback: treat as buffer from last tokenized id
            token = re.split(r'\s+', re.sub(r'[\(\)]', '', rhs))[-1]
            src = token
            self._net(pin_in_net)
            self._net(src)
            self.add_instance(f"assign_{pin_in_net}", "buf1", {"in1": src, "z": pin_in_net}, synthetic=True)
            # No alias unless it's a clean identifier
            if RE_RHS_ID.match(token):
                self.aliases[pin_in_net] = {"display": token, "invert": False, "kind": "top_in"}

    def add_assign_general(self, lhs: str, rhs: str):
        """
        General assign: synthetic buf/inv to LHS. Tag LHS as top_out (port) if desired.
        We keep the previous behavior: LHS is considered a top output port binding.
        """
        kind, data, inv = self._analyze_rhs(rhs)
        ctype = "inv1" if (kind == "id" and inv) else "buf1"
        in_net = data if kind in ("id", "const") else re.split(r'\s+', re.sub(r'[\(\)]', '', rhs))[-1]
        self._net(lhs)
        self._net(in_net)
        # Treat LHS as top output (matches earlier Step 2 behavior)
        self.tag_top_out(lhs)
        self.add_instance(f"assign_{lhs}", ctype, {"in1": in_net, "z": lhs}, synthetic=True)

    def finalize(self) -> dict:
        # Warn on multi-driver nets
        for net, info in sorted(self.nets.items()):
            if len(info["drivers"]) > 1:
                print(f"[WARN] Net '{net}' has multiple drivers: {info['drivers']}", file=sys.stderr)

        # Deterministic sort
        instances_sorted = sorted(self.instances, key=lambda d: (d["type"], d["name"]))
        nets_sorted = {}
        for n, info in sorted(self.nets.items()):
            nets_sorted[n] = {
                "drivers": sorted(info["drivers"], key=lambda x: (x[0], x[1])),
                "loads":   sorted(info["loads"],   key=lambda x: (x[0], x[1])),
                "tags":    sorted(set(info.get("tags", [])))
            }
        return {
            "version": 1,
            "celllib_ref": "celllib.json",
            "top": {
                # ONLY real external inputs (RHS ids) appear here
                "inputs":  sorted(self.top_inputs),
                "outputs": sorted(self.top_outputs)
            },
            "instances": instances_sorted,
            "nets": nets_sorted,
            "aliases": dict(sorted(self.aliases.items(), key=lambda kv: kv[0])),
            "constants": sorted(self.constants)
        }

# ----- Parsers -----

def parse_components(path: Path) -> List[Tuple[str,str,Dict[str,str]]]:
    """
    Parse structural instances from components.v
    Returns: list of (type, name, {pin: net})
    """
    txt = path.read_text(errors='ignore')
    txt_nc = strip_line_comments(txt)
    instances: List[Tuple[str,str,Dict[str,str]]] = []

    for m in RE_MODULE_INST.finditer(txt_nc):
        ctype, iname, body = m.groups()
        pins: Dict[str, str] = {}
        for pin, net in RE_NAMED_CONN.findall(body):
            pins[pin] = net.strip()
        instances.append((ctype, iname, pins))

    return instances

def parse_assigns(path: Path) -> List[Tuple[str,str]]:
    """
    Returns list of (LHS, RHS) from 'assign LHS = RHS;'
    RHS is not simplified here; GraphBuilder decides buf vs inv and aliasing.
    """
    txt = path.read_text(errors='ignore')
    txt_nc = strip_line_comments(txt)
    assigns = []
    for m in RE_ASSIGN.finditer(txt_nc):
        lhs, rhs = m.groups()
        assigns.append((lhs.strip(), rhs.strip()))
    return assigns

# ----- Main -----

def main():
    ap = argparse.ArgumentParser(description="Step 2 (Option A): Build netgraph.json with PIN_IN_* aliases.")
    ap.add_argument("--celllib", required=True, help="Path to celllib.json (from Step 1)")
    ap.add_argument("--components", required=True, help="Path to mioc_components.v")
    ap.add_argument("--assigns", required=True, help="Path to mioc_pin_assignments.v")
    ap.add_argument("--out", required=True, help="Path to write netgraph.json")
    args = ap.parse_args()

    # Load celllib
    celllib_path = Path(args.celllib)
    try:
        celllib_data = json.loads(celllib_path.read_text(errors='ignore'))
    except Exception as e:
        print(f"[E] Failed to read celllib: {e}", file=sys.stderr)
        sys.exit(1)
    celllib = CellLib(celllib_data)

    # Parse inputs
    comp_path = Path(args.components)
    insts = parse_components(comp_path)

    assigns_path = Path(args.assigns)
    assigns = parse_assigns(assigns_path)

    # Build graph
    gb = GraphBuilder(celllib)

    # Structural instances
    for ctype, iname, pins in insts:
        gb.add_instance(iname, ctype, pins, synthetic=False)

    # Assigns
    for lhs, rhs in assigns:
        if lhs.startswith("PIN_IN_"):
            gb.add_assign_pin_in(lhs, rhs)
        else:
            gb.add_assign_general(lhs, rhs)

    # Finalize and write
    graph = gb.finalize()
    outp = Path(args.out)
    outp.write_text(json.dumps(graph, indent=2))
    print(f"[OK] Wrote netgraph: {outp}")

if __name__ == "__main__":
    main()
