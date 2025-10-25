# === VNLT REV ===
# file: builder_verilog.py
# rev:  2025-10-19 06:29  r4  by:Drater  tag:builder
# note: flat netlist builder — parses module IO, assign, and instance hookups (.PIN(net));
#       outputs instances[name]={{type,pins{{pin:net}}}}, nets{{net:{{drivers,loads}}}}, top_inputs, top_outputs.
#       r4+dbg — env-guarded prints with prefix 'builder_verilog'.
# === /VNLT REV ===

import re, json, os
from typing import List, Dict, Tuple, Any

def _dbg(msg: str, *args):
    try:
        if not bool(int(os.getenv('VNLT_DEBUG','0') or '0')):  # env-only (no interp here)
            return
    except Exception:
        return
    try:
        text = msg % args if args else msg
    except Exception:
        text = f"{msg} | args={args}"
    print(f"builder_verilog: {text}")

WS = r"[\t\r\n ]*"
IDENT = r"[A-Za-z_][A-Za-z0-9_$]*"
NUM   = r"(?:\d+'[hdobHDOB][0-9a-fA-F_xXzZ]+|\d+)"
NETTOK = fr"(?:{IDENT}|{NUM})"
PIN    = fr"\.{IDENT}\({NETTOK}\)"
PINLIST = fr"{PIN}(?:{WS},{WS}{PIN})*"

_module_hdr_re = re.compile(fr"module{WS}({IDENT}){WS}\((.*?)\){WS};", re.S)
_endmodule_re = re.compile(r"endmodule\b")
_dir_decl_re = re.compile(fr"\b(input|output)\b(.*?);", re.S)
_wire_decl_re = re.compile(fr"\b(wire|tri|supply0|supply1)\b(.*?);", re.S)
_assign_re = re.compile(fr"\bassign\b{WS}({IDENT}){WS}={WS}({NETTOK}){WS};")
_inst_re = re.compile(fr"\b({IDENT}){WS}({IDENT}){WS}\(({WS}.*?{WS})\){WS};", re.S)
_pin_kv_re = re.compile(fr"\.{IDENT}\({NETTOK}\)")

def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    return text

def _split_modules(text: str) -> List[Tuple[str,str,str]]:
    out = []
    pos = 0
    while True:
        m = _module_hdr_re.search(text, pos)
        if not m: break
        name = m.group(1); ports = m.group(2)
        body_start = m.end()
        m_end = _endmodule_re.search(text, body_start)
        if not m_end: break
        body = text[body_start:m_end.start()]
        out.append((name, ports, body))
        pos = m_end.end()
    return out

def _parse_portlist(raw: str) -> List[str]:
    if not raw.strip(): return []
    parts = [p.strip() for p in raw.split(',')]
    return [p for p in parts if p]

def _parse_io_decls(body: str) -> Tuple[List[str], List[str]]:
    ins, outs = [], []
    for m in _dir_decl_re.finditer(body):
        direction = m.group(1)
        names = [x.strip() for x in re.split(r"[ ,]+", m.group(2)) if x.strip() and x.strip() not in ('[',';',']')]
        names = [n for n in names if not re.match(r"^\[.*\]$", n)]
        if direction == 'input':  ins.extend(names)
        if direction == 'output': outs.extend(names)
    return ins, outs

def _parse_assigns(body: str) -> List[Tuple[str,str]]:
    pairs = []
    for m in _assign_re.finditer(body):
        lhs, rhs = m.group(1), m.group(2)
        pairs.append((lhs, rhs))
    return pairs

def _parse_inst_pins(argstr: str) -> Dict[str,str]:
    pins = {}
    for m in _pin_kv_re.finditer(argstr):
        full = m.group(0)
        pin = full.split('(')[0][1:]
        net = full.split('(')[1].split(')')[0]
        pins[pin] = net
    return pins

def _parse_instances(body: str) -> List[Dict[str,Any]]:
    out = []
    for m in _inst_re.finditer(body):
        ctype, iname, argstr = m.group(1), m.group(2), m.group(3)
        pins = _parse_inst_pins(argstr)
        out.append({'name': iname, 'type': ctype, 'pins': pins})
    return out

def _choose_top(mods: List[Tuple[str,str,str]]) -> int:
    best_i = 0; best_score = -1
    for i, (_n,_p,body) in enumerate(mods):
        score = len(_inst_re.findall(body))
        if score > best_score:
            best_score = score; best_i = i
    return best_i

def build(files: List[str]) -> Tuple[Dict, Dict]:
    cell = build_celllib(files)
    graph = build_netgraph(files, cell)
    return cell, graph

def build_celllib(files: List[str]) -> Dict:
    _dbg("build_celllib: files=%d", len(files or []))
    text = "\n".join(_strip_comments(open(f, 'r', errors='ignore').read()) for f in files)
    mods = _split_modules(text)
    types = set()
    for _n,_p,body in mods:
        for m in _inst_re.finditer(body):
            types.add(m.group(1))
    return {
        'name': 'synth_celllib',
        'types': sorted(types),
        'pin_dirs': {},
        'is_seq':   {},
    }

def build_netgraph(files: List[str], celllib: Dict = None) -> Dict:
    _dbg("build_netgraph: files=%d", len(files or []))
    text = "\n".join(_strip_comments(open(f, 'r', errors='ignore').read()) for f in files)
    _dbg("split modules...")
    mods = _split_modules(text)
    if not mods:
        return {
            'top_inputs': [], 'top_outputs': [], 'instances': {}, 'nets': {}, 'aliases': {}, 'constants': {}
        }
    top_i = _choose_top(mods)
    top_name, top_ports, top_body = mods[top_i]

    top_in, top_out = _parse_io_decls(top_body)
    if not top_in and not top_out:
        plist = _parse_portlist(top_ports)
        top_in, top_out = [], []

    _dbg("parse assigns + instances...")
    assigns = _parse_assigns(top_body)
    instances = _parse_instances(top_body)

    inst_dict = {inst['name']: {'type': inst['type'], 'pins': inst['pins']} for inst in instances}

    nets_seen = set()
    for inst in instances:
        nets_seen.update(inst['pins'].values())
    for lhs, rhs in assigns:
        nets_seen.add(lhs); nets_seen.add(rhs)
    nets_seen.update(top_in); nets_seen.update(top_out)

    nets = {n: {'drivers': [], 'loads': []} for n in sorted(nets_seen)}
    OUT_PINS = {'Y','Q','Z','ZN','QN','ZBAR','QB','OUT','O'}
    IN_PINS  = {'A','B','C','D','IN','I0','I1','I2','I3'}
    for iname, info in inst_dict.items():
        pins = info.get('pins', {})
        for pin, net in pins.items():
            up = pin.upper()
            if up in OUT_PINS or up.startswith('O'):
                nets.setdefault(net, {'drivers': [], 'loads': []})['drivers'].append(f"{iname}.{pin}")
            elif up in IN_PINS or up.startswith('A') or up.startswith('I'):
                nets.setdefault(net, {'drivers': [], 'loads': []})['loads'].append(f"{iname}.{pin}")
            else:
                nets.setdefault(net, {'drivers': [], 'loads': []})['loads'].append(f"{iname}.{pin}")
    for lhs, rhs in assigns:
        nets.setdefault(lhs, {'drivers': [], 'loads': []})
        nets.setdefault(rhs, {'drivers': [], 'loads': []})
        nets[lhs]['drivers'].append(f"$assign.{rhs}")
        nets[rhs]['loads'].append(f"$assign->{lhs}")

    _dbg("graph: top=%s ins=%d outs=%d insts=%d nets=%d", top_name, len(top_in), len(top_out), len(inst_dict), len(nets))
    graph = {
        'name': top_name,
        'top_inputs': sorted(set(top_in)),
        'top_outputs': sorted(set(top_out)),
        'instances': inst_dict,
        'nets': nets,
        'aliases': {}, 'constants': {}
    }
    return graph

# === VNLT REV ===
# add: build_from_manifest shim  2025-10-19 06:45  r5  by:Drater
# === /VNLT REV ===

def _collect_verilog_files_from_cfg(cfg):
    files = []

    def add_if_verilog(x):
        if not isinstance(x, str): return
        s = x.strip()
        if s.endswith((".v", ".sv", ".vh", ".svh")):
            files.append(s)

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                # common keys
                if k.lower() in ("files","verilog","rtl","netlist","sources"):
                    walk(v); continue
                add_if_verilog(k); walk(v)
        elif isinstance(obj, (list, tuple, set)):
            for v in obj: walk(v)
        else:
            add_if_verilog(obj)

    walk(cfg or {})
    # Dedup, preserve order
    seen = set(); out = []
    for f in files:
        if f not in seen:
            seen.add(f); out.append(f)
    return out

def build_from_manifest(cfg):
    files = _collect_verilog_files_from_cfg(cfg)
    cell = build_celllib(files)
    graph = build_netgraph(files, cell)
    try:
        from gates import Interpreter
        interp = Interpreter()
        if hasattr(interp, "load_celllib_graph"):
            interp.load_celllib_graph(cell, graph)
            return interp
        import types
        G = types.SimpleNamespace(**graph)
        interp.celllib = cell
        interp.graph = G
        return interp
    except Exception:
        return (cell, graph)
