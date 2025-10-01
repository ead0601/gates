
from typing import List, Tuple, Dict
from registry import CommandRegistry
from core import Interpreter
import fnmatch
import os, time

SUMMARY = "list <files|components|instances|pins|port|nets> [...] — inventory views"
DETAIL = """\
Usage:
  list files
  list components [--like PATTERN] [--seq|--comb] [--ports]
  list instances [--like PATTERN] [--type CTYPE] [--seq|--comb]
  list pins <INSTANCE> | [--like 'U*.A*']
  list port [--like PATTERN]
  list nets [--like PATTERN] [--dangling] [--multi-driver] [--show-ends] [--limit N]

Notes:
  - Globs use shell-style patterns (* ? [abc]), case-sensitive.
  - Use --limit with --show-ends to cap verbose expansions.
"""

def _like(seq, pat):
    if not pat:
        return list(seq)
    return [s for s in seq if fnmatch.fnmatch(s, pat)]

def _fmt_cols(rows: List[Tuple], headers: Tuple[str, ...]) -> str:
    rows2 = [headers] + [tuple(map(str, r)) for r in rows]
    widths = [max(len(r[i]) for r in rows2) for i in range(len(headers))]
    out = []
    for i, r in enumerate(rows2):
        line = "  ".join((str(c).ljust(widths[j]) for j, c in enumerate(r)))
        out.append(line)
        if i == 0:
            out.append("  ".join("-"*w for w in widths))
    out.append(f"{len(rows)} rows")
    return "\n".join(out) + "\n"

def _list_files(interp: Interpreter):
    info = getattr(interp, "manifest_info", None)
    if not info:
        return {"__raw":"No manifest info available. Load a design first with: read verilog <manifest.lst>\n"}
    rows = []
    for kind in ("rtl","components","assigns"):
        for p in info.get(kind, []):
            try:
                st = os.stat(p)
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                rows.append((kind, p, "ok", st.st_size, mtime))
            except FileNotFoundError:
                rows.append((kind, p, "missing", "-", "-"))
    hdr = ("KIND","PATH","STATUS","SIZE","MTIME")
    return {"__raw": _fmt_cols(rows, hdr)}

def _list_components(interp: Interpreter, args: List[str]):
    if not interp.celllib:
        return {"__raw":"No design loaded.\n"}
    like = None; want_seq=None; show_ports=False
    it = iter(args)
    for a in it:
        if a == "--like": like = next(it)
        elif a == "--seq": want_seq=True
        elif a == "--comb": want_seq=False
        elif a == "--ports": show_ports=True
        else: return {"__raw": DETAIL}
    names = sorted(interp.celllib.pin_dir.keys())
    if like: names = _like(names, like)
    rows = []
    for c in names:
        is_seq = interp.celllib.is_sequential(c)
        if want_seq is not None and is_seq != want_seq:
            continue
        pd = interp.celllib.pin_dir_of(c)
        ins = sum(1 for d in pd.values() if d=="in")
        outs= sum(1 for d in pd.values() if d=="out")
        inst_count = sum(1 for inst in (interp.graph.instances or {}).values() if inst.get("type")==c) if interp.graph else 0
        rows.append((c, "seq" if is_seq else "comb", f"{ins}/{outs}", inst_count, ",".join(sorted(pd.keys())) if show_ports else ""))
    hdr = ("NAME","CLASS","PINS(in/out)","INSTANCES","PORTS" if show_ports else "")
    if not show_ports:
        rows = [r[:4] for r in rows]
        hdr = hdr[:4]
    return {"__raw": _fmt_cols(rows, hdr)}

def _list_instances(interp: Interpreter, args: List[str]):
    if not interp.graph:
        return {"__raw":"No design loaded.\n"}
    like=None; ctype=None; want_seq=None
    it = iter(args)
    for a in it:
        if a == "--like": like = next(it)
        elif a == "--type": ctype = next(it)
        elif a == "--seq": want_seq=True
        elif a == "--comb": want_seq=False
        else: return {"__raw": DETAIL}
    names = sorted(interp.graph.instances.keys())
    if like: names = _like(names, like)
    rows = []
    for iname in names:
        inst = interp.graph.instances[iname]
        t = inst.get("type","")
        if ctype and t != ctype: continue
        if want_seq is not None and interp.celllib and interp.celllib.is_sequential(t) != want_seq: 
            continue
        pins = inst.get("pins") or {}
        fanin = sum(1 for p,n in pins.items() if interp.celllib.pin_dir_of(t).get(p)=="in") if interp.celllib else 0
        fanout= sum(1 for p,n in pins.items() if interp.celllib.pin_dir_of(t).get(p)=="out") if interp.celllib else 0
        rows.append((iname, t, fanin, fanout, len(pins)))
    hdr=("NAME","TYPE","FANIN","FANOUT","NETS")
    return {"__raw": _fmt_cols(rows, hdr)}

def _list_pins(interp: Interpreter, args: List[str]):
    if not interp.graph:
        return {"__raw":"No design loaded.\n"}
    target=None; like=None
    it = iter(args)
    for a in it:
        if a == "--like": like = next(it)
        else:
            target = a
    rows = []
    if target:
        inst = interp.graph.instances.get(target)
        if not inst:
            return {"__raw": f"Unknown instance: {target}\n"}
        t = inst.get("type","")
        pd = interp.celllib.pin_dir_of(t) if interp.celllib else {}
        for pin, net in sorted((inst.get("pins") or {}).items()):
            rows.append((target, pin, pd.get(pin,"?"), net))
    else:
        # glob over INST.PIN
        pat = like or "*"
        for iname, inst in interp.graph.instances.items():
            t = inst.get("type","")
            pd = interp.celllib.pin_dir_of(t) if interp.celllib else {}
            for pin, net in (inst.get("pins") or {}).items():
                if fnmatch.fnmatch(f"{iname}.{pin}", pat):
                    rows.append((iname, pin, pd.get(pin,"?"), net))
        rows.sort(key=lambda x: (x[0], x[1]))
    hdr=("INST","PIN","DIR","NET")
    return {"__raw": _fmt_cols(rows, hdr)}

def _list_port(interp: Interpreter, args: List[str]):
    if not interp.graph:
        return {"__raw":"No design loaded.\n"}
    like=None
    it = iter(args)
    for a in it:
        if a == "--like": like = next(it)
        else: return {"__raw": DETAIL}
    rows = []
    for p in sorted(interp.graph.top_inputs):
        if like and not fnmatch.fnmatch(p, like): continue
        rows.append((p, "in", p))
    for p in sorted(interp.graph.top_outputs):
        if like and not fnmatch.fnmatch(p, like): continue
        rows.append((p, "out", p))
    hdr=("PORT","DIR","NET")
    return {"__raw": _fmt_cols(rows, hdr)}

def _list_nets(interp: Interpreter, args: List[str]):
    if not interp.graph:
        return {"__raw":"No design loaded.\n"}
    like=None; dangling=False; md=False; show=False; limit=20
    it = iter(args)
    for a in it:
        if a == "--like": like = next(it)
        elif a == "--dangling": dangling=True
        elif a == "--multi-driver": md=True
        elif a == "--show-ends": show=True
        elif a == "--limit": limit=int(next(it))
        else: return {"__raw": DETAIL}
    rows = []
    for n, nd in interp.graph.nets.items():
        if like and not fnmatch.fnmatch(n, like): continue
        drivers = sorted(list(nd.get("drivers", [])))
        loads   = sorted(list(nd.get("loads", [])))
        if dangling and (len(drivers)==0 or len(loads)==0):
            pass
        elif md and len(drivers) > 1:
            pass
        elif not dangling and not md:
            pass
        else:
            continue
        if show:
            dstr = ",".join(f"{i}.{p}" for i,p in drivers[:limit])
            lstr = ",".join(f"{i}.{p}" for i,p in loads[:limit])
            rows.append((n, len(drivers), len(loads), dstr, lstr))
        else:
            rows.append((n, len(drivers), len(loads)))
    hdr = ("NET","DRIVERS","#LOADS") if not show else ("NET","DRIVERS","#LOADS","DRIVER_LIST","LOAD_LIST")
    return {"__raw": _fmt_cols(rows, hdr)}

def _handler(args: List[str], interp: Interpreter):
    if not args:
        return {"__raw": DETAIL}
    sub = args[0]
    if sub == "files":
        return _list_files(interp)
    elif sub == "components":
        return _list_components(interp, args[1:])
    elif sub == "instances":
        return _list_instances(interp, args[1:])
    elif sub == "pins":
        return _list_pins(interp, args[1:])
    elif sub == "port":
        return _list_port(interp, args[1:])
    elif sub == "nets":
        return _list_nets(interp, args[1:])
    else:
        return {"__raw": DETAIL}

def register(reg: CommandRegistry):
    reg.add_command("list", _handler, SUMMARY, DETAIL)
