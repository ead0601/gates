# === VNLT REV ===
# file: python/builders.py
# rev:  2025-10-03  r1  by:ediaz  tag:show
# note: initial per-file revision header; show single instance/net details
# === /VNLT REV ===

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

_re_line_comment = re.compile(r"//.*$")
_re_block_comment = re.compile(r"/\*.*?\*/", re.S)

def _slurp(path: Path) -> str:
    try:
        text = path.read_text(errors="ignore")
    except FileNotFoundError:
        raise FileNotFoundError(f"source not found: {path}")
    text = _re_block_comment.sub("", text)
    lines = []
    for ln in text.splitlines():
        ln = _re_line_comment.sub("", ln)
        lines.append(ln)
    return "\n".join(lines)

def _parse_ident_list(s: str) -> List[str]:
    return [p.strip() for p in s.split(",") if p.strip()]

def build_celllib(rtl_files: List[str], seq_cells: List[str]) -> Dict:
    cells: Dict[str, Dict] = {}
    seq_set = set(seq_cells or [])

    re_module = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*(\([^;]*\))?\s*;")
    re_endmodule = re.compile(r"\bendmodule\b")
    re_io_ansi = re.compile(r"\b(input|output)\b([^;]*);")
    re_io_nonansi = re.compile(r"\b(input|output)\b\s+([^;]+);")

    for rf in rtl_files:
        p = Path(rf)
        src = _slurp(p)
        i = 0
        while True:
            m = re_module.search(src, i)
            if not m: break
            name = m.group(1)
            inputs: Set[str] = set()
            outputs: Set[str] = set()
            m2 = re_endmodule.search(src, m.end())
            body = src[m.end(): m2.start()] if m2 else src[m.end():]

            for mm in re_io_nonansi.finditer(body):
                dirn = mm.group(1)
                rhs = mm.group(2)
                rhs = re.sub(r"\[[^\]]+\]", " ", rhs)
                rhs = re.sub(r"\bwire\b|\breg\b|\bsigned\b|\bunsigned\b", " ", rhs)
                pins = _parse_ident_list(rhs)
                for pin in pins:
                    if dirn == "input": inputs.add(pin)
                    else: outputs.add(pin)

            if not inputs and not outputs and m.group(2):
                plist = m.group(2)
                for mm in re_io_ansi.finditer(plist):
                    dirn = mm.group(1)
                    rhs = mm.group(2)
                    rhs = re.sub(r"\[[^\]]+\]", " ", rhs)
                    rhs = re.sub(r"\bwire\b|\breg\b|\bsigned\b|\bunsigned\b", " ", rhs)
                    pins = _parse_ident_list(rhs)
                    for pin in pins:
                        if not re.match(r"[A-Za-z_]\w*$", pin): 
                            continue
                        if dirn == "input": inputs.add(pin)
                        else: outputs.add(pin)

            cells[name] = {
                "name": name,
                "category": "seq" if name in seq_set else "comb",
                "inputs": sorted(inputs),
                "outputs": sorted(outputs)
            }
            i = m2.end() if m2 else len(src)

    cells.setdefault("iobuf", {"name":"iobuf","category":"comb","inputs":["in1"],"outputs":["z"]})
    cells.setdefault("iobuf_n", {"name":"iobuf_n","category":"comb","inputs":["in1"],"outputs":["z"]})
    cells.setdefault("buf1", {"name":"buf1","category":"comb","inputs":["in1"],"outputs":["z"]})
    cells.setdefault("inv1", {"name":"inv1","category":"comb","inputs":["in1"],"outputs":["z"]})

    return {"cells": cells}

_re_inst = re.compile(
    r"^\s*([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\(\s*([^;]*)\);\s*$",
    re.M | re.S
)
_re_pinmap = re.compile(r"\.\s*([A-Za-z_]\w*)\s*\(\s*([^\)]+)\)")
_re_assign = re.compile(r"^\s*assign\s+(.+?)\s*=\s*(.+?)\s*;\s*$", re.M)
_re_decl_io = re.compile(r"^\s*(input|output)\s+([^;]+);\s*$", re.M)

def _normalize_net_token(tok: str) -> str:
    return tok.strip()

def _const_kind(tok: str) -> str:
    t = tok.replace(" ", "")
    if t in ("1'b0","1'b1","1h0","1h1","1d0","1d1"):
        return t
    return ""

def _parse_top_ios(top_src: str) -> Tuple[Set[str], Set[str]]:
    top_in, top_out = set(), set()
    for m in _re_decl_io.finditer(top_src):
        dirn = m.group(1)
        rhs = m.group(2)
        rhs = re.sub(r"\[[^\]]+\]", " ", rhs)
        rhs = re.sub(r"\bwire\b|\breg\b|\bsigned\b|\bunsigned\b", " ", rhs)
        pins = [p.strip() for p in rhs.split(",") if p.strip()]
        for p in pins:
            if dirn == "input": top_in.add(p)
            else: top_out.add(p)
    return top_in, top_out

def build_netgraph(celllib: Dict, components_files: List[str], assigns_files: List[str], top: str) -> Dict:

    io_counter = 0  # for iobuf instance naming
    nets: Dict[str, Dict[str, Set[tuple]]] = {}
    instances: List[Dict] = []
    aliases: Dict[str, Dict] = {}
    constants: Set[str] = set()
    top_inputs: Set[str] = set()
    top_outputs: Set[str] = set()
    cell_pin_dir: Dict[str, Dict[str, str]] = {}

    for ctype, meta in (celllib.get("cells") or {}).items():
        ins = meta.get("inputs", []) or []
        outs = meta.get("outputs", []) or []
        pd = {p: "in" for p in ins}
        for p in outs: pd[p] = "out"
        cell_pin_dir[ctype] = pd

    comp_concat = "\n".join(_slurp(Path(cf)) for cf in components_files)
    m_top = re.search(rf"\bmodule\s+{re.escape(top)}\b\s*\([^;]*\)\s*;(?P<body>.*?)\bendmodule\b", comp_concat, re.S)
    if not m_top:
        top_body = comp_concat
    else:
        top_body = m_top.group("body")
        ti, to = _parse_top_ios(top_body)
        top_inputs |= ti
        top_outputs |= to
        # emit iobuf from top_body assigns (no need for assigns: in manifest)
        for am in _re_assign.finditer(top_body):
            lhs = am.group(1).strip()
            rhs = am.group(2).strip()
            inv = False
            mtil = re.match(r"~\s*(.+)$", rhs)
            if mtil:
                inv = True
                rhs = mtil.group(1).strip()
            ck = _const_kind(rhs)
            in_net = rhs
            if ck:
                constants.add(ck)
                in_net = ck
            ctype = "iobuf_n" if inv else "iobuf"
            io_counter += 1
            iname = f"io{io_counter}"
            instances.append({"name": iname, "type": ctype, "pins": {"in1": in_net, "z": lhs}})

    for m in _re_inst.finditer(top_body):
        ctype, iname, plist = m.group(1), m.group(2), m.group(3)
        pinmap = {}
        for pm in _re_pinmap.finditer(plist):
            pin, net = pm.group(1), _normalize_net_token(pm.group(2))
            net = re.sub(r"[{}]", "", net).strip()
            pinmap[pin] = net
        instances.append({"name": iname, "type": ctype, "pins": pinmap})

    for af in assigns_files:
        src = _slurp(Path(af))
        for am in _re_assign.finditer(src):
            lhs = am.group(1).strip()
            rhs = am.group(2).strip()
            inv = False
            mtil = re.match(r"~\s*(.+)$", rhs)
            if mtil:
                inv = True
                rhs = mtil.group(1).strip()
            ck = _const_kind(rhs)
            in_net = rhs
            if ck:
                constants.add(ck)
                in_net = ck
            ctype = "iobuf_n" if inv else "iobuf"
            io_counter += 1
            iname = f"io{io_counter}"
            instances.append({"name": iname, "type": ctype, "pins": {"in1": in_net, "z": lhs}})

            if re.match(r"PIN_IN_\d+$", lhs):
                aliases[lhs] = {"display": rhs if not ck else rhs, "invert": inv, "kind": "top_in"}
            elif re.match(r"PIN_OUT_\d+$", lhs):
                aliases[lhs] = {"display": rhs if not ck else rhs, "invert": inv, "kind": "top_out"}
                top_outputs.add(lhs)
            elif lhs in top_inputs:
                aliases[lhs] = {"display": rhs if not ck else rhs, "invert": inv, "kind": "top_in"}
            elif lhs in top_outputs:
                aliases[lhs] = {"display": rhs if not ck else rhs, "invert": inv, "kind": "top_out"}

    def _add_load(net: str, iname: str, pin: str):
        if net not in nets:
            nets[net] = {"drivers": set(), "loads": set()}
        nets[net]["loads"].add((iname, pin))

    def _add_drv(net: str, iname: str, pin: str):
        if net not in nets:
            nets[net] = {"drivers": set(), "loads": set()}
        nets[net]["drivers"].add((iname, pin))

    for inst in instances:
        iname = inst["name"]
        ctype = inst["type"]
        pd = cell_pin_dir.get(ctype, {})
        for pin, net in (inst.get("pins") or {}).items():
            if pd.get(pin) == "out":
                _add_drv(net, iname, pin)
            else:
                _add_load(net, iname, pin)

    for n in top_inputs | top_outputs | constants:
        nets.setdefault(n, {"drivers": set(), "loads": set()})

    nets2 = {}
    for n, d in nets.items():
        nets2[n] = {
            "drivers": sorted(d["drivers"], key=lambda x:(x[0], x[1])),
            "loads":   sorted(d["loads"], key=lambda x:(x[0], x[1])),
        }

    return {
        "top": {"name": top, "inputs": sorted(list(top_inputs)), "outputs": sorted(list(top_outputs))},
        "instances": instances,
        "nets": nets2,
        "aliases": aliases,
        "constants": sorted(list(constants)),
        "meta": {"generated_by": "vnlt builders.py"}
    }
